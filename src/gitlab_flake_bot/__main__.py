from pathlib import Path

import structlog
import typer

from . import platform
from .settings import settings
from .update import process_project


@typer.run
def main(config: Path = typer.Option("config.toml", help="Path to configuration file")):
    settings.load(config)

    log = structlog.get_logger()

    for project in platform.client.projects.list(
        iterator=True, membership=True, with_merge_requests_enabled=True, archived=False, min_access_level=30
    ):
        log = log.bind(project=project.path_with_namespace)

        try:
            process_project(project, settings, log)
        except Exception:
            log.exception("Failed to process project")
            raise


if __name__ == "__main__":
    main()
