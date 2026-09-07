from pathlib import Path

import pytest

from ai_project_health_monitor.ingestion.connectors.synthetic_document import (
    SyntheticDocumentConnector,
)


def test_synthetic_document_connector_returns_project_events(
    tmp_path: Path,
) -> None:
    document = tmp_path / "project-001-status.md"
    document.write_text(
        "# Project Status\n\nThe project is delayed.",
        encoding="utf-8",
    )

    connector = SyntheticDocumentConnector(tmp_path)

    events = connector.fetch_events("PROJ-001")

    assert len(events) == 1
    assert events[0].project_id == "PROJ-001"
    assert events[0].source_type.value == "document"
    assert events[0].source_id == "project-001-status.md"
    assert "project is delayed" in events[0].content
    assert events[0].metadata["file_type"] == "markdown"


def test_synthetic_document_connector_ignores_documents_from_other_projects(
    tmp_path: Path,
) -> None:
    project_001_document = tmp_path / "project-001-status.md"
    project_001_document.write_text(
        "Project 001 is delayed.",
        encoding="utf-8",
    )

    project_002_document = tmp_path / "project-002-status.md"
    project_002_document.write_text(
        "Project 002 is on track.",
        encoding="utf-8",
    )

    connector = SyntheticDocumentConnector(tmp_path)

    events = connector.fetch_events("PROJ-001")

    assert len(events) == 1
    assert events[0].project_id == "PROJ-001"
    assert events[0].source_id == "project-001-status.md"


def test_synthetic_document_connector_returns_no_events_for_project_without_documents(
    tmp_path: Path,
) -> None:
    document = tmp_path / "project-001-status.md"
    document.write_text(
        "Project 001 is delayed.",
        encoding="utf-8",
    )

    connector = SyntheticDocumentConnector(tmp_path)

    events = connector.fetch_events("PROJ-002")

    assert events == []


def test_synthetic_document_connector_ignores_empty_documents(
    tmp_path: Path,
) -> None:
    empty_document = tmp_path / "project-001-status.md"
    empty_document.write_text("   ", encoding="utf-8")

    connector = SyntheticDocumentConnector(tmp_path)

    events = connector.fetch_events("PROJ-001")

    assert events == []


def test_synthetic_document_connector_ignores_non_markdown_files(
    tmp_path: Path,
) -> None:
    markdown = tmp_path / "project-001-status.md"
    markdown.write_text(
        "Project update.",
        encoding="utf-8",
    )

    text_file = tmp_path / "project-001-notes.txt"
    text_file.write_text(
        "Should be ignored.",
        encoding="utf-8",
    )

    connector = SyntheticDocumentConnector(tmp_path)

    events = connector.fetch_events("PROJ-001")

    assert len(events) == 1
    assert events[0].source_id == "project-001-status.md"


def test_synthetic_document_connector_rejects_empty_project_id(
    tmp_path: Path,
) -> None:
    connector = SyntheticDocumentConnector(tmp_path)

    with pytest.raises(ValueError, match="project_id cannot be empty"):
        connector.fetch_events("   ")


def test_synthetic_document_connector_rejects_invalid_document_filename(
    tmp_path: Path,
) -> None:
    document = tmp_path / "status.md"
    document.write_text(
        "Project status.",
        encoding="utf-8",
    )

    connector = SyntheticDocumentConnector(tmp_path)

    with pytest.raises(
        ValueError,
        match="Unable to determine project ID",
    ):
        connector.fetch_events("PROJ-001")