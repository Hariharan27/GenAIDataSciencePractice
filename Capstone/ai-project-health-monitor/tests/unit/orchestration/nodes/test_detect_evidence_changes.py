from datetime import UTC, datetime

import pytest

from ai_project_health_monitor.domain.models.health_score import HealthStatus
from ai_project_health_monitor.orchestration.nodes.detect_evidence_changes import (
    DetectEvidenceChangesNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.persistence.health_snapshot import (
    ProjectHealthSnapshot,
)


def _snapshot(fingerprint: str) -> ProjectHealthSnapshot:
    return ProjectHealthSnapshot(
        project_id="PROJ-001",
        health_score=81.0,
        health_status=HealthStatus.HEALTHY,
        risk_signals=[],
        calculated_at=datetime(2026, 9, 1, tzinfo=UTC),
        evidence_fingerprint=fingerprint,
    )


def test_detects_change_when_no_previous_snapshot_exists() -> None:
    node = DetectEvidenceChangesNode()
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        evidence_fingerprint="current-fingerprint",
    )

    result = node(state)

    assert result["evidence_changed"] is True


def test_detects_no_change_when_fingerprints_match() -> None:
    node = DetectEvidenceChangesNode()
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        evidence_fingerprint="same-fingerprint",
        previous_health_snapshot=_snapshot("same-fingerprint"),
    )

    result = node(state)

    assert result["evidence_changed"] is False


def test_detects_change_when_fingerprints_differ() -> None:
    node = DetectEvidenceChangesNode()
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
        evidence_fingerprint="new-fingerprint",
        previous_health_snapshot=_snapshot("old-fingerprint"),
    )

    result = node(state)

    assert result["evidence_changed"] is True


def test_requires_current_evidence_fingerprint() -> None:
    node = DetectEvidenceChangesNode()
    state = ProjectHealthState(
        project_id="PROJ-001",
        query="project health",
    )

    with pytest.raises(
        ValueError,
        match="evidence_fingerprint must be available",
    ):
        node(state)