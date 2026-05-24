import logging
import json
import os
from datetime import datetime
# FIXED: Added Tuple to the import list from typing
from typing import Dict, Any, List, Optional, Union, Tuple 
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger(__name__)

# --- Configuration Constants ---
ETHICAL_PRINCIPLES_FILE = "backend/governance/ethical_principles.json"

# --- Enums for Ethical Status and Severity ---
class EthicalStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    FLAGGED = "flagged" # For warnings or areas needing review

class EthicalSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"

# --- Pydantic Models for Ethical Principles ---
class EthicalPrinciple(BaseModel):
    """
    Defines a single ethical principle that Priv adheres to.
    """
    principle_id: str = Field(..., description="Unique identifier for the principle.")
    name: str = Field(..., description="Human-readable name of the principle.")
    description: str = Field(..., description="Detailed description of the principle's intent.")
    category: str = Field(..., description="Category of the principle (e.g., 'fairness', 'transparency', 'risk_management').")
    severity: EthicalSeverity = Field(EthicalSeverity.MEDIUM, description="Default severity of violating this principle.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Configurable parameters for the principle's evaluation (e.g., 'max_drawdown_percent').")
    # A reference to the actual Python function that evaluates this principle
    check_function_name: str = Field(..., description="Name of the function/method to call for evaluation.")

class EthicalScaffoldingManager:
    """
    Manages Priv's ethical compliance by loading, activating, and evaluating
    ethical principles against its decisions.
    """
    def __init__(self, principles_definitions_path: str = ETHICAL_PRINCIPLES_FILE):
        self.principles_definitions_path = principles_definitions_path
        self.all_principles: Dict[str, EthicalPrinciple] = {}
        self.active_principles: List[EthicalPrinciple] = []
        self._load_principles()
        logger.info("Priv: EthicalScaffoldingManager initialized.")
    
    def get_active_principles_ids(self) -> list[str]:
        """Return the IDs of all currently active ethical principles."""
        return [principle.id for principle in self.active_principles]


    def _load_principles(self):
        """Loads ethical principles from a JSON file."""
        if not os.path.exists(self.principles_definitions_path):
            logger.warning(f"Priv: Ethical principles file not found at {self.principles_definitions_path}. No ethical principles loaded.")
            return

        try:
            with open(self.principles_definitions_path, "r", encoding="utf-8") as f:
                raw_principles = json.load(f)
                for principle_data in raw_principles:
                    try:
                        principle = EthicalPrinciple(**principle_data)
                        self.all_principles[principle.principle_id] = principle
                    except Exception as e:
                        logger.error(f"Priv: Error parsing ethical principle {principle_data.get('principle_id', 'Unknown')}: {e}")
            logger.info(f"Priv: Loaded {len(self.all_principles)} ethical principles.")
        except Exception as e:
            logger.error(f"Priv: Error loading ethical principles from {self.principles_definitions_path}: {e}", exc_info=True)
            self.all_principles = {}

    def activate_principles_for_persona(self, persona: Dict[str, Any]):
        """
        Activates a subset of principles based on the AI's persona or user settings.
        For simplicity, activates all loaded principles, but can be selective.
        """
        self.active_principles = []
        for principle_id, principle in self.all_principles.items():
            self.active_principles.append(principle)
        logger.info(f"Priv: Activated {len(self.active_principles)} ethical principles for persona '{persona.get('name', 'N/A')}'.")

    def check_ethical_compliance(self,
                                 proposed_action: Dict[str, Any],
                                 current_context: Dict[str, Any],
                                 agent_persona: Dict[str, Any]
                                 ) -> Dict[str, Any]:
        """
        Evaluates a proposed action against all active ethical principles.

        Args:
            proposed_action (Dict[str, Any]): The action proposed by Priv (e.g., trade details).
            current_context (Dict[str, Any]): The current market and account context.
            agent_persona (Dict[str, Any]): The persona/risk profile of the agent proposing.

        Returns:
            Dict[str, Any]: A dictionary containing overall status ('compliant', 'non_compliant', 'flagged')
                            and a list of any violations.
        """
        violations: List[Dict[str, Any]] = []
        overall_status = EthicalStatus.COMPLIANT

        for principle in self.active_principles:
            check_function = getattr(self, principle.check_function_name, None)
            if check_function:
                # FIXED: CapitalPreservationPrinciple now correctly returns a Tuple
                is_compliant, violation_details = check_function(principle, proposed_action, current_context, agent_persona)
                if not is_compliant:
                    violations.append(violation_details)
                    if principle.severity == EthicalSeverity.CRITICAL:
                        overall_status = EthicalStatus.NON_COMPLIANT
                    elif overall_status != EthicalStatus.NON_COMPLIANT:
                        overall_status = EthicalStatus.FLAGGED
            else:
                logger.warning(f"Priv: Ethical principle '{principle.name}' has no corresponding check function '{principle.check_function_name}'.")

        return {"status": overall_status.value, "violations": violations}

    # --- Example Ethical Check Functions (corresponding to check_function_name) ---
    def CapitalPreservationPrinciple(self, principle: EthicalPrinciple, proposed_action: Dict[str, Any], current_context: Dict[str, Any], agent_persona: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Checks for excessive drawdown or risk beyond defined limits for capital preservation.
        Parameters: max_drawdown_percent, risk_tolerance_threshold
        """
        max_drawdown_pct = principle.parameters.get("max_drawdown_percent", 0.10)
        account_drawdown = current_context.get("account_drawdown", 0.0)
        
        trade_risk_pct = proposed_action.get("risk_assessment", {}).get("per_trade_risk_pct", 0.0)
        portfolio_risk_pct = current_context.get("portfolio_total_risk_pct", 0.0)

        risk_tolerance_threshold_str = principle.parameters.get("risk_tolerance_threshold", "medium")
        agent_risk_tolerance = agent_persona.get("risk_tolerance", "medium")

        effective_max_drawdown = max_drawdown_pct
        if agent_risk_tolerance == "low":
            effective_max_drawdown = max_drawdown_pct * 0.5
        elif agent_risk_tolerance == "high":
            effective_max_drawdown = max_drawdown_pct * 1.5
        
        if (account_drawdown > effective_max_drawdown) or \
           (portfolio_risk_pct + trade_risk_pct > effective_max_drawdown * 2):
            return False, {
                "principle_id": principle.principle_id,
                "name": principle.name,
                "severity": principle.severity.value,
                "message": f"Excessive drawdown ({account_drawdown:.2%}) or portfolio risk ({portfolio_risk_pct:.2%}) exceeds {effective_max_drawdown:.2%} limit for '{agent_persona.get('name')}' persona."
            }
        return True, None

    def MarketIntegrityPrinciple(self, principle: EthicalPrinciple, proposed_action: Dict[str, Any], current_context: Dict[str, Any], agent_persona: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Checks for actions that could manipulate the market (e.g., excessively large volume for illiquid asset).
        Parameters: max_volume_impact_pct (e.g., max 1% of daily volume)
        """
        max_volume_impact_pct = principle.parameters.get("max_volume_impact_pct", 0.01)
        proposed_volume = proposed_action.get("volume", 0.0)
        contract_size = current_context.get("contract_size", 100000)
        avg_daily_volume = current_context.get("avg_daily_volume", 1.0)

        total_trade_units = proposed_volume * contract_size if "forex" in proposed_action.get("symbol", "").lower() else proposed_volume

        if avg_daily_volume > 0 and total_trade_units / avg_daily_volume > max_volume_impact_pct:
            return False, {
                "principle_id": principle.principle_id,
                "name": principle.name,
                "severity": principle.severity.value,
                "message": f"Proposed trade volume ({proposed_volume}) is too large ({total_trade_units/avg_daily_volume:.2%}) relative to average daily volume, potential market impact."
            }
        return True, None

    def ResponsibleTradingPrinciple(self, principle: EthicalPrinciple, proposed_action: Dict[str, Any], current_context: Dict[str, Any], agent_persona: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Checks for excessive frequency or over-exposure to news-sensitive events.
        Parameters: max_trades_per_hour, news_trading_avoidance_impact ("high", "medium")
        """
        news_trading_status = current_context.get("news_trading_status", "NORMAL_TRADING_CONDITIONS").upper()
        llm_market_impact = current_context.get("llm_market_impact", "none").upper()
        
        avoid_impact_level = principle.parameters.get("news_trading_avoidance_impact", "high").upper()

        if (avoid_impact_level == "HIGH" and ("PRE_NEWS_PAUSE" in news_trading_status or "POST_NEWS_VOLATILITY" in news_trading_status or llm_market_impact == "HIGH")) or \
           (avoid_impact_level == "MEDIUM" and (("PRE_NEWS_PAUSE" in news_trading_status or "POST_NEWS_VOLATILITY" in news_trading_status) and llm_market_impact in ["HIGH", "MEDIUM"])):
            return False, {
                "principle_id": principle.principle_id,
                "name": principle.name,
                "severity": principle.severity.value,
                "message": f"Proposed trade during restricted news period ({news_trading_status}) or high LLM market impact ({llm_market_impact})."
            }
        return True, None

# Example Usage (for testing EthicalScaffoldingManager in isolation)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    mock_principles_content = [
        {
            "principle_id": "CP_HighDrawdown",
            "name": "Capital Preservation",
            "description": "Prevent excessive drawdown relative to risk tolerance.",
            "category": "risk_management",
            "severity": "critical",
            "parameters": {"max_drawdown_percent": 0.05, "risk_tolerance_threshold": "medium"},
            "check_function_name": "CapitalPreservationPrinciple"
        },
        {
            "principle_id": "MI_LargeVolume",
            "name": "Market Integrity",
            "description": "Avoid trades that could unduly influence market price (too large volume).",
            "category": "market_conduct",
            "severity": "high",
            "parameters": {"max_volume_impact_pct": 0.005},
            "check_function_name": "MarketIntegrityPrinciple"
        },
        {
            "principle_id": "RT_NewsAvoidance",
            "name": "Responsible Trading - News Avoidance",
            "description": "Avoid trading during volatile news periods based on impact level.",
            "category": "trading_behavior",
            "severity": "medium",
            "parameters": {"news_trading_avoidance_impact": "high"},
            "check_function_name": "ResponsibleTradingPrinciple"
        }
    ]
    temp_principles_file = "temp_ethical_principles.json"
    os.makedirs(os.path.dirname(temp_principles_file), exist_ok=True)
    with open(temp_principles_file, "w") as f:
        json.dump(mock_principles_content, f, indent=2)
    logger.info(f"Mock ethical principles saved to {temp_principles_file}")

    manager = EthicalScaffoldingManager(principles_definitions_path=temp_principles_file)
    
    test_persona_medium_risk = {"name": "Test Trader", "risk_tolerance": "medium"}
    manager.activate_principles_for_persona(test_persona_medium_risk)

    print("\n--- Test Case 1: Compliant Trade ---")
    proposed_action_1 = {"symbol": "EURUSD", "volume": 0.1, "risk_assessment": {"per_trade_risk_pct": 0.005}}
    current_context_1 = {"account_drawdown": 0.01, "portfolio_total_risk_pct": 0.02, "contract_size": 100000, "avg_daily_volume": 1000000, "news_trading_status": "NORMAL_TRADING_CONDITIONS", "llm_market_impact": "none"}
    
    compliance_result_1 = manager.check_ethical_compliance(proposed_action_1, current_context_1, test_persona_medium_risk)
    print(f"Compliance Result 1: {compliance_result_1['status']}, Violations: {compliance_result_1['violations']}")

    print("\n--- Test Case 2: Capital Preservation Violation ---")
    proposed_action_2 = {"symbol": "GBPUSD", "volume": 0.5, "risk_assessment": {"per_trade_risk_pct": 0.01}}
    current_context_2 = {"account_drawdown": 0.07, "portfolio_total_risk_pct": 0.08, "contract_size": 100000, "avg_daily_volume": 500000, "news_trading_status": "NORMAL_TRADING_CONDITIONS", "llm_market_impact": "none"}
    
    compliance_result_2 = manager.check_ethical_compliance(proposed_action_2, current_context_2, test_persona_medium_risk)
    print(f"Compliance Result 2: {compliance_result_2['status']}, Violations: {compliance_result_2['violations']}")

    print("\n--- Test Case 3: Market Integrity Violation (Excessive Volume) ---")
    proposed_action_3 = {"symbol": "ILLIQUID_STOCK", "volume": 5000, "risk_assessment": {"per_trade_risk_pct": 0.01}}
    current_context_3 = {"account_drawdown": 0.01, "portfolio_total_risk_pct": 0.02, "contract_size": 1, "avg_daily_volume": 10000, "news_trading_status": "NORMAL_TRADING_CONDITIONS", "llm_market_impact": "none"}
    
    compliance_result_3 = manager.check_ethical_compliance(proposed_action_3, current_context_3, test_persona_medium_risk)
    print(f"Compliance Result 3: {compliance_result_3['status']}, Violations: {compliance_result_3['violations']}")

    print("\n--- Test Case 4: Responsible Trading Violation (News Avoidance) ---")
    proposed_action_4 = {"symbol": "EURJPY", "volume": 0.1, "risk_assessment": {"per_trade_risk_pct": 0.005}}
    current_context_4 = {"account_drawdown": 0.01, "portfolio_total_risk_pct": 0.02, "contract_size": 100000, "avg_daily_volume": 1000000, "news_trading_status": "PRE_NEWS_PAUSE: USD NFP in 5 minutes.", "llm_market_impact": "high"}
    
    compliance_result_4 = manager.check_ethical_compliance(proposed_action_4, current_context_4, test_persona_medium_risk)
    print(f"Compliance Result 4: {compliance_result_4['status']}, Violations: {compliance_result_4['violations']}")

    if os.path.exists(temp_principles_file):
        os.remove(temp_principles_file)
        logger.info(f"Cleaned up mock ethical principles file: {temp_principles_file}")

__all__ = [
    "EthicalStatus",
    "EthicalSeverity",
    "EthicalPrinciple",
    "EthicalScaffoldingManager",
    "ComplianceStatus"
]
