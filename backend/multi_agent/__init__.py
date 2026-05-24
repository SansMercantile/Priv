"""PRIV multi-agent package.

This package previously imported most agents eagerly at module import time,
which pulled in heavy broker/data-science dependencies and made unrelated API
modules fail to import. Keep exports lazy so lightweight modules such as the
agent reputation/vote ledgers can be used without bootstrapping the full stack.
"""

from importlib import import_module

__all__ = [
    "MultiAgentSystem",
    "BaseAgent",
    "TaskRequest",
    "TaskResult",
    "AgentStatus",
    "AgentPriority",
    "AgentInfo",
    "PrivQuantitativeAgent",
    "QuantitativeAgent",
    "PrivTechnicalAgent",
    "FundamentalAgent",
    "PrivEconomicAgent",
    "PrivPoliticalAgent",
    "PrivSentimentAgent",
    "PrivRiskAgent",
    "PrivComplianceAgent",
    "PrivArbitrageAgent",
    "PrivForexAgent",
    "PrivOptionsAgent",
    "PrivFuturesAgent",
    "AgentReputationLedger",
    "ArbitrationEngine",
    "CorporateMemoryGraph",
    "CentralOrchestrator",
    "EscalationEngine",
    "CollaborativeIntelligence",
    "PrivAgentProtocol",
    "MessageType",
    "MessageBrokerInterface",
    "GoogleCloudPubSubBroker",
]

_LAZY_IMPORTS = {
    "MultiAgentSystem": (".multi_agent_system", "MultiAgentSystem"),
    "BaseAgent": (".multi_agent_system", "BaseAgent"),
    "TaskRequest": (".multi_agent_system", "TaskRequest"),
    "TaskResult": (".multi_agent_system", "TaskResult"),
    "AgentStatus": (".multi_agent_system", "AgentStatus"),
    "AgentPriority": (".multi_agent_system", "AgentPriority"),
    "AgentInfo": (".multi_agent_system", "AgentInfo"),
    "PrivQuantitativeAgent": (".priv_quantitative_agent", "PrivQuantitativeAgent"),
    "QuantitativeAgent": (".priv_quantitative_agent", "PrivQuantitativeAgent"),
    "PrivTechnicalAgent": (".priv_technical_agent", "PrivTechnicalAgent"),
    "FundamentalAgent": (".fundamental_agent", "FundamentalAgent"),
    "PrivEconomicAgent": (".priv_economic_agent", "PrivEconomicAgent"),
    "PrivPoliticalAgent": (".priv_political_agent", "PrivPoliticalAgent"),
    "PrivSentimentAgent": (".priv_sentiment_agent", "PrivSentimentAgent"),
    "PrivRiskAgent": (".priv_risk_agent", "PrivRiskAgent"),
    "PrivComplianceAgent": (".priv_compliance_agent", "PrivComplianceAgent"),
    "PrivArbitrageAgent": (".priv_arbitrage_agent", "PrivArbitrageAgent"),
    "PrivForexAgent": (".priv_forex_agent", "PrivForexAgent"),
    "PrivOptionsAgent": (".priv_options_agent", "PrivOptionsAgent"),
    "PrivFuturesAgent": (".priv_futures_agent", "PrivFuturesAgent"),
    "AgentReputationLedger": (".agent_reputation_ledger", "AgentReputationLedger"),
    "ArbitrationEngine": (".arbitration_engine", "ArbitrationEngine"),
    "CorporateMemoryGraph": (".corporate_memory_graph", "CorporateMemoryGraph"),
    "CentralOrchestrator": (".central_orchestrator", "CentralOrchestrator"),
    "EscalationEngine": (".escalation_engine", "EscalationEngine"),
    "CollaborativeIntelligence": (".collaborative_intelligence", "CollaborativeIntelligence"),
    "PrivAgentProtocol": (".priv_agent_protocol", "PrivAgentProtocol"),
    "MessageType": (".priv_agent_protocol", "MessageType"),
    "MessageBrokerInterface": (".message_broker_interface", "MessageBrokerInterface"),
    "GoogleCloudPubSubBroker": (".message_broker_interface", "GoogleCloudPubSubBroker"),
}


def __getattr__(name):
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _LAZY_IMPORTS[name]
    module = import_module(module_name, __name__)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(__all__)