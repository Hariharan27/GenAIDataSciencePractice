import re
from datetime import UTC, datetime
from pathlib import Path

from ai_project_health_monitor.domain.models.project_event import (
    ProjectEvent,
    SourceType,
)
from ai_project_health_monitor.ingestion.connectors.base import (
    ProjectSourceConnector,
)


class SyntheticDocumentConnector(ProjectSourceConnector):
    """Read synthetic project documents from a directory."""

    PROJECT_ID_PATTERN = re.compile(
        r"^project-(\d+)-.+\.md$",
        re.IGNORECASE,
    )

    def __init__(self, source_directory: Path) -> None:
        self._source_directory = source_directory

    def fetch_events(self, project_id: str) -> list[ProjectEvent]:
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        events: list[ProjectEvent] = []

        for document_path in sorted(
            self._source_directory.glob("*.md")
        ):
            document_project_id = self._extract_project_id(
                document_path
            )

            if document_project_id != project_id.upper():
                continue

            content = document_path.read_text(
                encoding="utf-8"
            )

            if not content.strip():
                continue

            events.append(
                ProjectEvent(
                    event_id=f"DOC-EVENT-{document_path.stem}",
                    project_id=document_project_id,
                    source_type=SourceType.DOCUMENT,
                    source_id=document_path.name,
                    content=content,
                    occurred_at=datetime.fromtimestamp(
                        document_path.stat().st_mtime,
                        tz=UTC,
                    ),
                    metadata={
                        "file_name": document_path.name,
                        "file_type": "markdown",
                    },
                )
            )

        return events

    @classmethod
    def _extract_project_id(
        cls,
        document_path: Path,
    ) -> str:
        match = cls.PROJECT_ID_PATTERN.match(
            document_path.name
        )

        if match is None:
            raise ValueError(
                "Unable to determine project ID from document "
                f"filename: {document_path.name}"
            )

        return f"PROJ-{match.group(1)}"