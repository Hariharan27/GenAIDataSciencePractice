from functools import lru_cache
from pathlib import Path

from qdrant_client import QdrantClient

from ai_project_health_monitor.analysis.deterministic_health_alert_evaluator import (
    DeterministicHealthAlertEvaluator,
)
from ai_project_health_monitor.analysis.deterministic_health_scorer import (
    DeterministicHealthScorer,
)
from ai_project_health_monitor.analysis.llm_factory import LLMClientFactory
from ai_project_health_monitor.analysis.llm_health_summary_generator import (
    LLMHealthSummaryGenerator,
)
from ai_project_health_monitor.analysis.llm_risk_analyzer import (
    LLMRiskAnalyzer,
)
from ai_project_health_monitor.analysis.risk_consolidator import (
    RiskConsolidator,
)
from ai_project_health_monitor.analysis.risk_grounding_validator import (
    DeterministicRiskGroundingValidator,
)
from ai_project_health_monitor.core.config import Settings, get_settings
from ai_project_health_monitor.ingestion.connectors.base import (
    ProjectSourceConnector,
)
from ai_project_health_monitor.ingestion.connectors.synthetic_document import (
    SyntheticDocumentConnector,
)
from ai_project_health_monitor.ingestion.connectors.synthetic_email import (
    SyntheticEmailConnector,
)
from ai_project_health_monitor.ingestion.connectors.synthetic_jira import (
    SyntheticJiraConnector,
)
from ai_project_health_monitor.ingestion.service import IngestionService
from ai_project_health_monitor.notifications.deterministic_alert_deduplicator import (
    DeterministicAlertDeduplicator,
)
from ai_project_health_monitor.notifications.deterministic_alert_escalator import (
    DeterministicAlertEscalator,
)
from ai_project_health_monitor.notifications.logging_alert_delivery import (
    LoggingAlertDelivery,
)
from ai_project_health_monitor.notifications.logging_alert_escalator_notifier import (
    LoggingAlertEscalatorNotifier,
)
from ai_project_health_monitor.notifications.logging_alert_notifier import (
    LoggingAlertNotifier,
)
from ai_project_health_monitor.notifications.logging_health_summary_delivery import (
    LoggingHealthSummaryDelivery,
)
from ai_project_health_monitor.notifications.logging_health_summary_notifier import (
    LoggingHealthSummaryNotifier,
)
from ai_project_health_monitor.observability.config import ObservabilityConfig
from ai_project_health_monitor.observability.instrumented_llm import (
    InstrumentedLLMClient,
)
from ai_project_health_monitor.observability.langfuse import LangfuseClient
from ai_project_health_monitor.orchestration.graph import (
    build_project_health_graph,
)
from ai_project_health_monitor.persistence.repositories.postgres_health_snapshot import (
    PostgresHealthSnapshotRepository,
)
from ai_project_health_monitor.rag.chunking import FixedSizeChunker
from ai_project_health_monitor.rag.embeddings.bge import BGEEmbeddingModel
from ai_project_health_monitor.rag.indexing import RAGIndexer
from ai_project_health_monitor.rag.project_health_retrieval import (
    ProjectHealthEvidenceRetriever,
)
from ai_project_health_monitor.rag.retrieval import RetrievalService
from ai_project_health_monitor.rag.vector_store.qdrant import (
    QdrantVectorStore,
)
from ai_project_health_monitor.services.health_monitor_scheduler import (
    HealthMonitorScheduler,
)
from ai_project_health_monitor.services.health_trend_service import (
    HealthTrendService,
)
from ai_project_health_monitor.services.llm_weekly_health_summary_generator import (
    LLMWeeklyHealthSummaryGenerator,
)
from ai_project_health_monitor.services.project_health_monitor import (
    ProjectHealthMonitor,
)
from ai_project_health_monitor.services.weekly_health_analysis_service import (
    WeeklyHealthAnalysisService,
)
from ai_project_health_monitor.services.weekly_health_history_service import (
    WeeklyHealthHistoryService,
)
from ai_project_health_monitor.services.weekly_health_summary_service import (
    WeeklyHealthSummaryService,
)
from ai_project_health_monitor.services.weekly_risk_evolution_service import (
    WeeklyRiskEvolutionService,
)
from ai_project_health_monitor.analysis.risk_change_detector import (
    RiskChangeDetector,
)
from ai_project_health_monitor.analysis.llm_risk_change_investigator import (
    LLMRiskChangeInvestigator,
)


class ApplicationContainer:
    """Own application-wide dependencies and the compiled health graph."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        self.embedding_model = BGEEmbeddingModel()

        qdrant_client = QdrantClient(
            url=settings.qdrant_url,
        )

        self.vector_store = QdrantVectorStore(
            client=qdrant_client,
            vector_size=384,
        )

        self.retrieval_service = RetrievalService(
            embedding_model=self.embedding_model,
            vector_store=self.vector_store,
        )

        self.health_snapshot_repository = PostgresHealthSnapshotRepository(
            dsn=settings.postgres_dsn,
        )

        self.project_health_evidence_retriever = ProjectHealthEvidenceRetriever(
            retrieval_service=self.retrieval_service,
        )

        llm_client = LLMClientFactory.create(settings)

        observability = LangfuseClient(
            ObservabilityConfig(
                enabled=settings.langfuse_enabled,
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
            )
        )

        self.llm_client = InstrumentedLLMClient(
            llm_client=llm_client,
            observability=observability,
        )

        # Historical health services
        self.health_trend_service = HealthTrendService(
            health_snapshot_repository=self.health_snapshot_repository,
        )

        self.weekly_health_history_service = WeeklyHealthHistoryService(
            health_snapshot_repository=self.health_snapshot_repository,
        )

        self.weekly_health_analysis_service = WeeklyHealthAnalysisService()

        self.weekly_risk_evolution_service = WeeklyRiskEvolutionService()

        # Weekly summary generation
        self.weekly_health_summary_generator = LLMWeeklyHealthSummaryGenerator(
            llm_client=self.llm_client,
        )

        self.weekly_health_summary_service = WeeklyHealthSummaryService(
            weekly_health_history_service=self.weekly_health_history_service,
            weekly_health_analysis_service=self.weekly_health_analysis_service,
            weekly_risk_evolution_service=self.weekly_risk_evolution_service,
            weekly_health_summary_generator=self.weekly_health_summary_generator,
        )

        # Risk analysis
        self.risk_analyzer = LLMRiskAnalyzer(
            llm_client=self.llm_client,
            grounding_validator=DeterministicRiskGroundingValidator(),
        )
        risk_consolidator = RiskConsolidator()
        risk_change_detector = RiskChangeDetector()
        risk_change_investigator = LLMRiskChangeInvestigator(
            llm_client=self.llm_client,
        )
        health_scorer = DeterministicHealthScorer()

        summary_generator = LLMHealthSummaryGenerator(
            llm_client=self.llm_client,
        )

        alert_evaluator = DeterministicHealthAlertEvaluator()

        # Alerting
        alert_delivery = LoggingAlertDelivery()
        notifier = LoggingAlertNotifier(alert_delivery)

        deduplicator = DeterministicAlertDeduplicator()
        escalator = DeterministicAlertEscalator()
        escalation_notifier = LoggingAlertEscalatorNotifier()

        # Summary delivery
        summary_delivery = LoggingHealthSummaryDelivery()
        summary_notifier = LoggingHealthSummaryNotifier(
            summary_delivery,
        )

        self.ingestion_service = IngestionService(
            connectors=self._build_connectors(settings),
        )

        self.graph = build_project_health_graph(
            evidence_retriever=self.project_health_evidence_retriever,
            risk_analyzer=self.risk_analyzer,
            risk_consolidator=risk_consolidator,
            risk_change_detector=risk_change_detector,
            risk_change_investigator=risk_change_investigator,
            health_scorer=health_scorer,
            summary_generator=summary_generator,
            alert_evaluator=alert_evaluator,
            notifier=notifier,
            deduplicator=deduplicator,
            escalator=escalator,
            escalation_notifier=escalation_notifier,
            summary_notifier=summary_notifier,
            health_snapshot_repository=self.health_snapshot_repository,
            ingestion_service=self.ingestion_service,
        )

        self.project_health_monitor = ProjectHealthMonitor(
            graph=self.graph,
            health_trend_service=self.health_trend_service,
        )

        self.health_monitor_scheduler = HealthMonitorScheduler(
            monitor=self.project_health_monitor,
        )

        self.rag_indexer = RAGIndexer(
            chunker=FixedSizeChunker(),
            embedding_model=self.embedding_model,
            vector_store=self.vector_store,
        )


    @staticmethod
    def _build_connectors(
        settings: Settings,
    ) -> list[ProjectSourceConnector]:
        return [
            SyntheticJiraConnector(
                source_path=Path(settings.jira_source_path),
            ),
            SyntheticEmailConnector(
                source_path=Path(settings.email_source_path),
            ),
            SyntheticDocumentConnector(
                source_directory=Path(settings.document_source_directory),
            ),
        ]


@lru_cache
def get_application_container() -> ApplicationContainer:
    """Return the singleton application dependency container."""
    return ApplicationContainer(get_settings())