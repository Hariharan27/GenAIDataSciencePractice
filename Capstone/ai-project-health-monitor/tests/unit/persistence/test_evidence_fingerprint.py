from datetime import UTC, datetime

from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.domain.models.project_event import SourceType
from ai_project_health_monitor.persistence.evidence_fingerprint import (
    EvidenceFingerprint,
)


def create_evidence(
    event_id: str,
    content: str,
) -> Evidence:
    return Evidence(
        event_id=event_id,
        source_type=SourceType.JIRA,
        source_id=f"source-{event_id}",
        content=content,
        occurred_at=datetime(2026, 9, 10, 10, tzinfo=UTC),
    )


def test_same_evidence_produces_same_fingerprint() -> None:
    evidence = [create_evidence("EVENT-001", "Backend is delayed.")]

    first = EvidenceFingerprint.calculate(evidence)
    second = EvidenceFingerprint.calculate(evidence)

    assert first == second


def test_evidence_order_does_not_change_fingerprint() -> None:
    first_evidence = create_evidence("EVENT-001", "Backend is delayed.")
    second_evidence = create_evidence("EVENT-002", "Client approved scope.")

    first = EvidenceFingerprint.calculate([first_evidence, second_evidence])
    second = EvidenceFingerprint.calculate([second_evidence, first_evidence])

    assert first == second


def test_changed_evidence_produces_different_fingerprint() -> None:
    first = EvidenceFingerprint.calculate(
        [create_evidence("EVENT-001", "Backend is delayed.")]
    )
    second = EvidenceFingerprint.calculate(
        [create_evidence("EVENT-001", "Backend is on schedule.")]
    )

    assert first != second


def test_empty_evidence_has_stable_fingerprint() -> None:
    first = EvidenceFingerprint.calculate([])
    second = EvidenceFingerprint.calculate([])

    assert first == second
    assert len(first) == 64