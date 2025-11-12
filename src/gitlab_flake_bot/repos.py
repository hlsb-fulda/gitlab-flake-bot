import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from hashlib import blake2b
from typing import Self

import sh
from gitlab.v4.objects import Project
from urllib.parse import urlparse, urlunparse

from . import platform
from .settings import settings


@dataclass
class Repository:
    project: Project

    hash: str
    path: Path

    @classmethod
    def clone(cls: Self, project: Project) -> Self:
        cache = settings.cache / "repos"
        cache.mkdir(parents=True, exist_ok=True)

        hash = blake2b(digest_size=10)
        hash.update(settings.gitlab.url.encode())
        hash.update(project.path_with_namespace.encode())
        hash = hash.hexdigest()

        path = cache / hash

        url = urlparse(project.http_url_to_repo)
        url = url._replace(netloc=f"gitlab-ci-token:{settings.gitlab.api_token}@{url.netloc}")
        url = urlunparse(url)

        # We move the currently existing repository to a backup location but use it as a reference while cloning the latest
        # version. This ensures that we don't download too much data on each clone.
        shutil.rmtree(path.with_suffix(".old"), ignore_errors=True)
        if path.exists():
            path.rename(path.with_suffix(".old"))

        sh.git.clone(
            url,
            path,
            reference_if_able=path.with_suffix(".old"),
            dissociate=True,
            depth=1,
            branch=project.default_branch,
            recurse_submodules=True,
        )

        shutil.rmtree(path.with_suffix(".old"), ignore_errors=True)

        return cls(
            project=project,
            hash=hash,
            path=path,
        )

    @property
    def git(self):
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = platform.client.user.name
        env["GIT_AUTHOR_EMAIL"] = platform.client.user.commit_email

        return sh.git.bake(_cwd=self.path, _env=env)

    @property
    def nix(self):
        return sh.nix.bake(_cwd=self.path)

    def is_dirty(self):
        diff = self.git.diff(quiet=True, exit_code=True, _ok_code=[0, 1], _return_cmd=True)
        return diff.exit_code != 0
