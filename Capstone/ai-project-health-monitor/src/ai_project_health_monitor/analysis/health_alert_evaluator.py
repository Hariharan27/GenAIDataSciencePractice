from abc import ABC, abstractmethod

from ai_project_health_monitor.domain.models.health_alert import HealthAlert
from ai_project_health_monitor.domain.models.health_score import HealthScore


class HealthAlertEvaluator(ABC):
    """Contract for evaluating whether project health requires an alert."""

    @abstractmethod
    def evaluate(self, health_score: HealthScore) -> HealthAlert:
        """Evaluate project health and produce an alert decision."""
        raise NotImplementedError