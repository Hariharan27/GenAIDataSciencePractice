from ai_project_health_monitor.ingestion.service import IngestionService
from ai_project_health_monitor.orchestration.state import ProjectHealthState
from ai_project_health_monitor.persistence.project_event_fingerprint import (
    ProjectEventFingerprint,
)


class CollectCurrentEvidenceNode:
    """Collect the current source events and calculate their fingerprint."""

    def __init__(
        self,
        ingestion_service: IngestionService,
    ) -> None:
        self._ingestion_service = ingestion_service

    def __call__(self, state: ProjectHealthState) -> dict[str, object]:
        events = self._ingestion_service.ingest_project(state.project_id)
        fingerprint = ProjectEventFingerprint.calculate(events)

        return {
            "evidence_fingerprint": fingerprint,
        }