from datetime import UTC, datetime

from ai_project_health_monitor.domain.models.project_event import (
    ProjectEvent,
    SourceType,
)
from ai_project_health_monitor.persistence.project_event_fingerprint import (
    ProjectEventFingerprint,
)


def _event(
    event_id: str = "EVT-001",
    content: str = "Payment API integration is blocked.",
) -> ProjectEvent:
    return ProjectEvent(
        event_id=event_id,
        project_id="PROJ-001",
        source_type=SourceType.JIRA,
        source_id="PROJ-101",
        content=content,
        author="alice",
        occurred_at=datetime(2026, 9, 1, tzinfo=UTC),
        metadata={"status": "blocked", "priority": "high"},
    )


def test_same_events_produce_same_fingerprint() -> None:
    events = [_event()]

    first = ProjectEventFingerprint.calculate(events)
    second = ProjectEventFingerprint.calculate(events)

    assert first == second
    assert len(first) == 64


def test_event_order_does_not_change_fingerprint() -> None:
    first_event = _event(event_id="EVT-001")
    second_event = _event(
        event_id="EVT-002",
        content="Testing is in progress.",
    )

    first = ProjectEventFingerprint.calculate(
        [first_event, second_event],
    )
    second = ProjectEventFingerprint.calculate(
        [second_event, first_event],
    )

    assert first == second


def test_changed_event_content_changes_fingerprint() -> None:
    original = ProjectEventFingerprint.calculate(
        [_event(content="Payment API integration is blocked.")],
    )
    changed = ProjectEventFingerprint.calculate(
        [_event(content="Payment API integration is resolved.")],
    )

    assert original != changed


def test_changed_metadata_changes_fingerprint() -> None:
    original_event = _event()
    changed_event = original_event.model_copy(
        update={"metadata": {"status": "resolved", "priority": "high"}},
    )

    original = ProjectEventFingerprint.calculate([original_event])
    changed = ProjectEventFingerprint.calculate([changed_event])

    assert original != changed


def test_empty_events_have_stable_fingerprint() -> None:
    first = ProjectEventFingerprint.calculate([])
    second = ProjectEventFingerprint.calculate([])

    assert first == second
    assert len(first) == 64