from ai_project_health_monitor.orchestration.state import ProjectHealthState


class DetectEvidenceChangesNode:
    """Determine whether current project evidence differs from the last analysis."""

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        if state.evidence_fingerprint is None:
            raise ValueError(
                "evidence_fingerprint must be available before detecting changes"
            )

        previous_snapshot = state.previous_health_snapshot

        if previous_snapshot is None:
            return {"evidence_changed": True}

        return {
            "evidence_changed": (
                state.evidence_fingerprint
                != previous_snapshot.evidence_fingerprint
            )
        }