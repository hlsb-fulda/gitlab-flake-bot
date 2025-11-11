import structlog

from .settings import settings
from .platform import gl
from .update import process_project


def main():
    log = structlog.get_logger()

    gl.auth()

    for project in gl.projects.list(iterator=True, membership=True, with_merge_requests_enabled=True, archived=False, min_access_level=30):
        log = log.bind(project=project.path_with_namespace)

        try:
            process_project(project, settings, log)
        except Exception:
            log.exception("Failed to process project")
            raise


if __name__ == "__main__":
    main()
