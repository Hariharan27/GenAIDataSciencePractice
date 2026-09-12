from ai_project_health_monitor.domain.models.evidence import Evidence
from ai_project_health_monitor.ingestion.connectors.synthetic_email import (
    SyntheticEmailConnector,
)
from ai_project_health_monitor.ingestion.connectors.synthetic_jira import (
    SyntheticJiraConnector,
)


class EvaluationEvidenceLoader:
    """Load normalized synthetic project events as evaluation evidence."""

    def __init__(
        self,
        jira_connector: SyntheticJiraConnector,
        email_connector: SyntheticEmailConnector,
    ) -> None:
        self._jira_connector = jira_connector
        self._email_connector = email_connector

    def load_by_event_id(
        self,
        project_id: str,
        event_ids: list[str],
    ) -> list[Evidence]:
        """Load evidence matching project and event IDs."""
        if not project_id.strip():
            raise ValueError("project_id cannot be empty")

        if not event_ids:
            return []

        events = (
            self._jira_connector.fetch_events(project_id)
            + self._email_connector.fetch_events(project_id)
        )

        events_by_id = {
            event.event_id: event
            for event in events
        }

        missing_event_ids = [
            event_id
            for event_id in event_ids
            if event_id not in events_by_id
        ]

        if missing_event_ids:
            raise ValueError(
                "Evaluation events not found for project "
                f"{project_id}: "
                + ", ".join(missing_event_ids)
            )

        return [
            Evidence(
                event_id=event.event_id,
                source_type=event.source_type,
                source_id=event.source_id,
                content=event.content,
                occurred_at=event.occurred_at,
            )
            for event_id in event_ids
            for event in [events_by_id[event_id]]
        ]