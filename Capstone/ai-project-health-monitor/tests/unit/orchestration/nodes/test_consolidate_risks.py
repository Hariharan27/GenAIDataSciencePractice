from unittest.mock import Mock

from ai_project_health_monitor.analysis.risk_consolidator import RiskConsolidator
from ai_project_health_monitor.domain.models.risk_group import RiskGroup
from ai_project_health_monitor.domain.models.risk_signal import RiskSignal
from ai_project_health_monitor.orchestration.nodes.consolidate_risks import (
    ConsolidateRisksNode,
)
from ai_project_health_monitor.orchestration.state import ProjectHealthState


def test_consolidate_risks_node_returns_groups_and_primary_risks() -> None:
    risk_consolidator = Mock(spec=RiskConsolidator)

    risk_signal = Mock(spec=RiskSignal)
    risk_group = Mock(spec=RiskGroup)

    risk_consolidator.consolidate.return_value = [risk_group]
    risk_consolidator.primary_risks.return_value = [risk_signal]

    node = ConsolidateRisksNode(
        risk_consolidator=risk_consolidator,
    )

    state = ProjectHealthState(
        project_id="PROJ-001",
        query="What risks are affecting the project?",
        risk_signals=[risk_signal],
    )

    result = node(state)

    assert result["risk_groups"] == [risk_group]
    assert result["primary_risks"] == [risk_signal]

    risk_consolidator.consolidate.assert_called_once_with(
        [risk_signal]
    )

    risk_consolidator.primary_risks.assert_called_once_with(
        [risk_group]
    )