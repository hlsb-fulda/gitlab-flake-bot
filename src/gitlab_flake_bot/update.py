import json
from typing import Optional
from datetime import datetime

import structlog
from gitlab.v4.objects import Project, ProjectCommit, MergeRequest
from munch import munchify

from . import platform
from .flake import Input
from .repos import Repository
from .settings import settings, Settings, RuleSettings
from .utils import gitlab_try, match_any, coalesce


def process_project(project: Project, settings: Settings, log: structlog.BoundLogger):
    log.debug(f"Processing project '{project.name_with_namespace}' ({project.id})")

    if not match_any(settings.projects, project.path_with_namespace):
        log.debug("Project does not match 'projects' filter - skipping")
        return

    log.info(f"Cloning repository: {project.http_url_to_repo}")
    repository = Repository.clone(project)

    if not (repository.path / "flake.nix").exists():
        log.info("No flake.nix found - skipping")
        return

    old_metadata = repository.nix.flake.metadata(json=True)
    old_metadata = json.loads(old_metadata)
    old_metadata = munchify(old_metadata)

    inputs = [
        Input(project=project.path_with_namespace, key=key, name=name, old=old_metadata.locks.nodes[name], new=None)
        for key, name in old_metadata.locks.nodes[old_metadata.locks.root].inputs.items()
    ]
    log.debug(f"Inputs found: {', '.join((input.key for input in inputs))}")

    for input in inputs:
        log = log.bind(input=input.key)

        rule = input.find_rule(settings.rules)
        if rule.ignore:
            log.debug("Input ignored by rule - skipping")
            continue

        # Check if input has been modified less than `interval` time ago
        last_modified = datetime.fromtimestamp(input.old.locked.lastModified)
        interval = coalesce(rule.interval, settings.interval)
        if interval is not None and last_modified + interval > datetime.now():
            log.debug("Input has been modified to recent - skipping", last_modified=last_modified, interval=interval)
            continue

        log.debug("Processing input...")

        process_input(repository, input, rule, log)


def process_input(repository: Repository, input: Input, rule: RuleSettings, log: structlog.BoundLogger):
    base_branch_name = repository.project.default_branch
    base_branch_commit = find_branch_head(repository.project, base_branch_name)

    branch_name = f"{settings.branch_prefix}{input.key}"
    branch_commit = find_branch_head(repository.project, branch_name)

    repository.git.fetch("origin", base_branch_name)

    if gitlab_try(repository.project.branches.get, branch_name) is None:
        # We don't have a branch yet - create one
        repository.git.checkout("-B", branch_name, "--")
        repository.git.reset(base_branch_commit.id, hard=True)

        branch_commit = base_branch_commit

    else:
        # Remote knows about branch - checkout it
        repository.git.fetch("origin", branch_name)
        repository.git.checkout("-B", branch_name, "--")
        repository.git.reset(branch_commit.id, hard=True)

        if branch_commit.author_name != platform.client.user.name or branch_commit.author_email != platform.client.user.commit_email:
            log.info("Last commit on branch was not created by this bot - skipping")
            return

    # Update flake input
    repository.nix.flake.update(input.key)

    # Process changes
    if repository.is_dirty():
        log.info("Changes detected - update available")

        # Reset to latest commit on base branch and apply update on top of that
        # This ensures that branches always contain a single commit and avoid merge conflicts
        repository.git.reset(base_branch_commit.id, hard=True)
        repository.nix.flake.update(input.key)

        # Get new metadata after update
        new_metadata = repository.nix.flake.metadata(json=True)
        new_metadata = json.loads(new_metadata)
        new_metadata = munchify(new_metadata)

        input.new = new_metadata.locks.nodes[input.name]

        message = settings.commit_message.format_map(input.__dict__)

        repository.git.add(".")
        repository.git.commit(message=message, no_signoff=True, no_verify=True, no_gpg_sign=True)
        repository.git.push("origin", f"HEAD:refs/heads/{branch_name}", force=True)

        # Update branch commit after push
        branch_commit = find_branch_head(repository.project, branch_name)

    if branch_commit.id == base_branch_commit.id:
        log.info("No update available - done")
        return

    # Ensure an up-to-date merge request exists
    merge_request = find_merge_request(repository.project, branch_name)
    if merge_request is None:
        log.info("No open MR found - creating")
        merge_request = repository.project.mergerequests.create(
            {
                "source_branch": branch_name,
                "target_branch": repository.project.default_branch,
                "title": branch_commit.title,
                "remove_source_branch": True,
            }
        )
    else:
        merge_request.title = branch_commit.title
        merge_request.save()

    log.debug(f"MR used: {merge_request.web_url}")

    # Check if the branch needs rebasing
    if merge_request.detailed_merge_status in ("need_rebase", "conflict"):
        log.debug("Branch needs rebasing")

        repository.git.reset(base_branch_commit.id, hard=True)
        repository.nix.flake.update(input.key)

        # Get new metadata after update
        new_metadata = repository.nix.flake.metadata(json=True)
        new_metadata = json.loads(new_metadata)
        new_metadata = munchify(new_metadata)

        input.new = new_metadata.locks.nodes[input.name]

        message = settings.commit_message.format_map(input.__dict__)

        repository.git.add(".")
        repository.git.commit(message=message, no_signoff=True, no_verify=True, no_gpg_sign=True)
        repository.git.push("origin", f"HEAD:refs/heads/{branch_name}", force=True)

        return

    if not coalesce(rule.auto_merge, settings.auto_merge):
        return

    if merge_request.detailed_merge_status != "mergeable":
        log.info("MR not mergeable yet", status=merge_request.detailed_merge_status)
        return

    if not all(status.status == "success" for status in branch_commit.statuses.list()):
        log.debug("MR not fully passed checks yet")
        return

    log.info("MR is mergeable and all checks passed - merging")
    merge_request.merge(should_remove_source_branch=True, merge_when_pipeline_succeeds=True)


def find_branch_head(project: Project, branch: str) -> Optional[ProjectCommit]:
    commits = project.commits.list(ref_name=branch, iterator=True)
    if commits is None:
        return None

    return next(commits, None)


def find_merge_request(project: Project, branch: str) -> Optional[MergeRequest]:
    merge_requests = project.mergerequests.list(
        state="opened",
        source_branch=branch,
        target_branch=project.default_branch,
        project_id=project.id,
        scope="created_by_me",
        with_merge_status_recheck=True,
        get_all=True,
    )

    if len(merge_requests) > 1:
        raise Exception("Multiple open MRs found")
    elif len(merge_requests) == 1:
        return merge_requests[0]
    else:
        return None
