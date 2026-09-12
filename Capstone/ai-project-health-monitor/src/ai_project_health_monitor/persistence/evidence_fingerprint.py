import hashlib
import json

from ai_project_health_monitor.domain.models.evidence import Evidence


class EvidenceFingerprint:
    """Create deterministic fingerprints for a project's current evidence."""

    @staticmethod
    def calculate(evidence: list[Evidence]) -> str:
        """Return a stable SHA-256 fingerprint for the supplied evidence."""
        canonical_evidence = sorted(
            (
                {
                    "event_id": item.event_id,
                    "source_type": item.source_type.value,
                    "source_id": item.source_id,
                    "content": item.content,
                    "occurred_at": item.occurred_at.isoformat(),
                }
                for item in evidence
            ),
            key=lambda item: (
                item["event_id"],
                item["source_type"],
                item["source_id"],
                item["occurred_at"],
                item["content"],
            ),
        )

        payload = json.dumps(
            canonical_evidence,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(payload).hexdigest()