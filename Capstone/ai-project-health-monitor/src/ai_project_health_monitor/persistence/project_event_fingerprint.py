import hashlib
import json

from ai_project_health_monitor.domain.models.project_event import ProjectEvent


class ProjectEventFingerprint:
    """Create deterministic fingerprints for a project's source events."""

    @staticmethod
    def calculate(events: list[ProjectEvent]) -> str:
        """Return a stable SHA-256 fingerprint for the supplied project events."""
        canonical_events = sorted(
            (
                {
                    "event_id": event.event_id,
                    "project_id": event.project_id,
                    "source_type": event.source_type.value,
                    "source_id": event.source_id,
                    "content": event.content,
                    "author": event.author,
                    "occurred_at": event.occurred_at.isoformat(),
                    "metadata": dict(sorted(event.metadata.items())),
                }
                for event in events
            ),
            key=lambda item: (
                item["event_id"],
                item["project_id"],
                item["source_type"],
                item["source_id"],
                item["occurred_at"],
            ),
        )

        payload = json.dumps(
            canonical_events,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(payload).hexdigest()