import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from pydantic import BaseModel, Field
from enum import Enum
import os
import json # NEW: Import json for loading rule definitions

logger = logging.getLogger(__name__)

# --- Enums for Rule Types and Compliance Status ---
class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    FLAGGED = "flagged" # Needs human review

class RuleCategory(str, Enum):
    TRADING_LIMITS = "trading_limits"
    ASSET_RESTRICTIONS = "asset_restrictions"
    REPORTING = "reporting"
    ETHICS = "ethics"
    DATA_PRIVACY = "data_privacy"
    OTHER = "other"

class RuleSeverity(str, Enum):
    CRITICAL = "critical" # Must comply, hard stop
    WARNING = "warning"   # Flag, may proceed with caution
    INFO = "info"         # For logging, no direct impact

# --- Pydantic Model for a Compliance Rule Definition ---
class ComplianceRuleDefinition(BaseModel):
    """Defines a single compliance rule to be loaded and enforced."""
    rule_id: str = Field(..., description="Unique ID for the rule (e.g., MiFID_II_Leverage_FX).")
    name: str = Field(..., description="Human-readable name of the rule.")
    description: str = Field(..., description="Detailed description of the rule.")
    category: RuleCategory = Field(..., description="Category of the rule.")
    severity: RuleSeverity = Field(RuleSeverity.CRITICAL, description="Severity of non-compliance.")
    jurisdictions: List[str] = Field(default_factory=list, description="List of jurisdictions this rule applies to (e.g., ['EU-MiFID', 'US-SEC']).") # Corrected example
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the rule's check function (e.g., {'max_leverage': 30}).")
    check_function_name: str = Field(..., description="Name of the function in ComplianceEngine to execute this rule.")

# --- Compliance Rule Base Class and Implementations ---
class ComplianceRule:
    """Base class for all compliance rules."""
    def __init__(self, definition: ComplianceRuleDefinition):
        self.definition = definition
        self.rule_id = definition.rule_id
        self.name = definition.name
        self.category = definition.category
        self.severity = definition.severity
        self.jurisdictions = definition.jurisdictions
        self.parameters = definition.parameters

    def check(self, trade_action: Dict[str, Any], current_context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Checks if a given trade action/context is compliant with this rule.
        Must be implemented by subclasses.

        Args:
            trade_action (Dict[str, Any]): The proposed trade action (e.g., from a TradeProposal).
            current_context (Dict[str, Any]): Relevant current market/account context.

        Returns:
            Tuple[bool, str]: (is_compliant, message). True for compliant, False for non-compliant.
        """
        raise NotImplementedError("Check method must be implemented by concrete rule classes.")

class MaxLeverageRule(ComplianceRule):
    """Example: Checks if a trade adheres to maximum leverage limits."""
    def __init__(self, definition: ComplianceRuleDefinition):
        super().__init__(definition)
        self.max_leverage = self.parameters.get("max_leverage", 100) # Default if not specified

    def check(self, trade_action: Dict[str, Any], current_context: Dict[str, Any]) -> Tuple[bool, str]:
        # This rule needs access to account equity, proposed trade value, and symbol details.
        # It's a complex calculation, typically: (volume * price) / (account_equity * max_leverage) should be <= 1
        
        proposed_volume = trade_action.get("volume", 0)
        entry_price = trade_action.get("entry_price", 0)
        account_equity = current_context.get("account_equity", 1)
        
        if account_equity <= 0 or proposed_volume <= 0 or entry_price <= 0:
            return True, "Cannot assess leverage: invalid input data." # Or log warning

        # Simplified check: if hypothetical trade value exceeds allowed leverage on equity
        trade_value_usd = proposed_volume * entry_price # Assuming base currency conversion
        
        # Max allowed trade value based on leverage: equity * max_leverage
        max_allowed_trade_value = account_equity * self.max_leverage
        
        if trade_value_usd > max_allowed_trade_value:
             return False, f"Proposed trade value (${trade_value_usd:.2f}) exceeds allowed max leverage of 1:{self.max_leverage} on equity (${account_equity:.2f})."
        
        return True, "Leverage compliant."

class RestrictedAssetRule(ComplianceRule):
    """Example: Checks if a trade is on a restricted asset for a given jurisdiction."""
    def __init__(self, definition: ComplianceRuleDefinition):
        super().__init__(definition)
        self.restricted_assets = [asset.upper() for asset in self.parameters.get("restricted_assets", [])] # Ensure uppercase for comparison

    def check(self, trade_action: Dict[str, Any], current_context: Dict[str, Any]) -> Tuple[bool, str]:
        symbol = trade_action.get("symbol", "").upper()
        if symbol in self.restricted_assets:
            return False, f"Asset '{symbol}' is restricted in this jurisdiction ({self.jurisdictions})."
        return True, "Asset is compliant."

class DummyVolatilityRule(ComplianceRule):
    """Placeholder for a rule that flags trades during high volatility."""
    def check(self, trade_action: Dict[str, Any], current_context: Dict[str, Any]) -> Tuple[bool, str]:
        volatility_threshold = self.parameters.get("volatility_threshold", 0.05)
        current_market_volatility = current_context.get("current_market_volatility", 0.0) # Assume this is available in context
        
        if current_market_volatility > volatility_threshold:
            return False, f"Market volatility ({current_market_volatility:.2%}) exceeds threshold ({volatility_threshold:.2%}), advise caution."
        return True, "Volatility is within acceptable limits."


# --- Compliance Engine (JRPPI Core) ---
class ComplianceEngine:
    """
    Manages loading, activating, and applying jurisdictional compliance rules.
    This serves as Priv's Jurisdictional Rule Plug-In Interface (JRPPI).
    """
    def __init__(self, rules_definitions_path: str = "backend/governance/compliance_rules.json"):
        self.rules_definitions_path = rules_definitions_path
        self.available_rules_definitions: Dict[str, ComplianceRuleDefinition] = {} # Rule ID -> Definition
        self.active_rules: List[ComplianceRule] = [] # Instantiated active rules
        self.current_jurisdiction_profile: Optional[str] = None # e.g., "MiFID II EU"
        self._rule_class_map: Dict[str, Callable[[ComplianceRuleDefinition], ComplianceRule]] = {
            "MaxLeverageRule": MaxLeverageRule,
            "RestrictedAssetRule": RestrictedAssetRule,
            "DummyVolatilityRule": DummyVolatilityRule, # Register the example dummy rule
            # Register other custom rule classes here as they are implemented
        }
        self._load_rule_definitions()
        logger.info("Priv's ComplianceEngine initialized.")
        
    def get_active_rules_ids(self) -> list[str]:
        """Return the IDs of all currently active compliance rules."""
        return [rule.rule_id for rule in self.active_rules]

    def _load_rule_definitions(self):
        """Loads rule definitions from a JSON file (simulating external plug-ins)."""
        if not os.path.exists(self.rules_definitions_path):
            logger.warning(f"Priv: Compliance rules definition file not found at: {self.rules_definitions_path}. No rules loaded.")
            return

        try:
            with open(self.rules_definitions_path, "r", encoding="utf-8") as f:
                raw_rules = json.load(f)
                for rule_data in raw_rules:
                    try:
                        rule_def = ComplianceRuleDefinition(**rule_data)
                        self.available_rules_definitions[rule_def.rule_id] = rule_def
                    except Exception as e:
                        logger.error(f"Priv: Error parsing rule definition {rule_data.get('rule_id', 'Unknown')}: {e}")
            logger.info(f"Priv: Loaded {len(self.available_rules_definitions)} compliance rule definitions.")
        except Exception as e:
            logger.error(f"Priv: Error loading compliance rule definitions from {self.rules_definitions_path}: {e}")

    def set_jurisdiction_profile(self, profile_name: str, enforce_rules: bool = True):
        """
        Activates rules relevant to a specific jurisdiction profile.
        This simulates loading a "regulatory dialect plugin".
        """
        self.current_jurisdiction_profile = profile_name
        self.active_rules = [] # Clear previously active rules
        
        for rule_id, rule_def in self.available_rules_definitions.items():
            # Activate rule if it applies to the current profile OR if profile is general/universal (empty jurisdictions list)
            if (profile_name in rule_def.jurisdictions or not rule_def.jurisdictions) and enforce_rules:
                rule_class = self._rule_class_map.get(rule_def.check_function_name)
                if rule_class:
                    try:
                        self.active_rules.append(rule_class(rule_def))
                    except Exception as e:
                        logger.error(f"Priv: Error instantiating rule '{rule_id}' ({rule_def.check_function_name}): {e}")
                else:
                    logger.warning(f"Priv: Unknown check function '{rule_def.check_function_name}' for rule '{rule_id}'. Rule not activated.")
            elif not enforce_rules:
                logger.info(f"Priv: Compliance engine in advisory mode for {profile_name}. No rules actively enforced.")
        
        logger.info(f"Priv: Activated {len(self.active_rules)} rules for jurisdiction profile: '{profile_name}'.")

    def check_compliance(self, trade_proposal: Dict[str, Any], current_context: Dict[str, Any]) -> Dict[str, Any]: # Changed from TradeProposal to Dict for flexibility
        """
        Checks a proposed trade action against all active compliance rules.

        Args:
            trade_proposal (Dict[str, Any]): The proposed trade action (e.g., from a TradeProposal's .model_dump()).
            current_context (Dict[str, Any]): Relevant current market/account context.

        Returns:
            Dict[str, Any]: Compliance status, list of violated rules, and total severity.
        """
        compliance_summary = {
            "status": ComplianceStatus.COMPLIANT,
            "violations": [],
            "total_critical_violations": 0,
            "total_warning_violations": 0
        }

        if not self.active_rules:
            logger.info("Priv: No active compliance rules to check against. Assuming compliant.")
            return compliance_summary

        for rule in self.active_rules:
            try:
                is_compliant, message = rule.check(trade_proposal, current_context)
                if not is_compliant:
                    violation_detail = {
                        "rule_id": rule.rule_id,
                        "name": rule.name,
                        "severity": rule.severity.value,
                        "message": message
                    }
                    compliance_summary["violations"].append(violation_detail)
                    
                    if rule.severity == RuleSeverity.CRITICAL:
                        compliance_summary["total_critical_violations"] += 1
                        compliance_summary["status"] = ComplianceStatus.NON_COMPLIANT
                    elif rule.severity == RuleSeverity.WARNING and compliance_summary["status"] != ComplianceStatus.NON_COMPLIANT:
                        compliance_summary["total_warning_violations"] += 1
                        compliance_summary["status"] = ComplianceStatus.FLAGGED

            except Exception as e:
                logger.error(f"Priv: Error checking rule '{rule.name}' for proposal: {e}", exc_info=True)
                # Treat rule check failure as a critical violation for safety
                compliance_summary["violations"].append({
                    "rule_id": rule.rule_id, "name": rule.name, "severity": RuleSeverity.CRITICAL.value,
                    "message": f"Rule check failed due to internal error: {e}"
                })
                compliance_summary["total_critical_violations"] += 1
                compliance_summary["status"] = ComplianceStatus.NON_COMPLIANT


        if compliance_summary["total_critical_violations"] > 0:
            compliance_summary["status"] = ComplianceStatus.NON_COMPLIANT
        elif compliance_summary["total_warning_violations"] > 0 and compliance_summary["status"] != ComplianceStatus.NON_COMPLIANT:
            compliance_summary["status"] = ComplianceStatus.FLAGGED
        
        logger.info(f"Priv: Compliance check for proposal {trade_proposal.get('symbol', 'N/A')} {trade_proposal.get('action', 'N/A')}: Status={compliance_summary['status'].value}, Violations={len(compliance_summary['violations'])}")
        return compliance_summary


# Example Usage (for testing the regulatory_compliance.py in isolation)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # --- Create a mock compliance_rules.json file ---
    mock_rules_content = [
        {
            "rule_id": "MiFID_II_Leverage_FX",
            "name": "MiFID II Forex Leverage Limit",
            "description": "Maximum 1:30 leverage for major FX pairs in EU.",
            "category": "trading_limits",
            "severity": "critical",
            "jurisdictions": ["EU-MiFID"],
            "parameters": {"max_leverage": 30},
            "check_function_name": "MaxLeverageRule"
        },
        {
            "rule_id": "SEC_Crypto_Ban",
            "name": "SEC Cryptocurrency Trading Ban",
            "description": "Trading of certain cryptocurrencies is prohibited for US-SEC regulated entities.",
            "category": "asset_restrictions",
            "severity": "critical",
            "jurisdictions": ["US-SEC"],
            "parameters": {"restricted_assets": ["BTCUSD", "ETHUSD"]},
            "check_function_name": "RestrictedAssetRule"
        },
        {
            "rule_id": "General_High_Vol_Warning",
            "name": "High Volatility Warning",
            "description": "Warns if trading during extremely high volatility.",
            "category": "trading_limits",
            "severity": "warning",
            "jurisdictions": [], # Applies universally if no specific jurisdiction
            "parameters": {"volatility_threshold": 0.05},
            "check_function_name": "DummyVolatilityRule"
        }
    ]
    compliance_rules_path = "backend/governance/compliance_rules.json"
    os.makedirs(os.path.dirname(compliance_rules_path), exist_ok=True)
    with open(compliance_rules_path, "w", encoding="utf-8") as f:
        json.dump(mock_rules_content, f, indent=2)
    logger.info(f"Mock compliance rules saved to {compliance_rules_path}")

    # --- Initialize ComplianceEngine ---
    compliance_engine = ComplianceEngine(rules_definitions_path=compliance_rules_path)

    # --- Test EU-MiFID Profile ---
    print("\n--- Testing EU-MiFID Compliance Profile ---")
    compliance_engine.set_jurisdiction_profile("EU-MiFID")

    # Mock TradeProposal (using dictionary equivalent as direct Pydantic import might create circular dep)
    mock_trade_prop1_low_leverage = {
        "symbol": "EURUSD", "action": "BUY", "volume": 0.01, "entry_price": 1.0850,
        "stop_loss": 1.0800, "take_profit": 1.0900, "reasoning": "Test", "confidence": 0.8,
        "risk_assessment": {}
    }
    mock_context1 = {"account_equity": 10000.0, "current_market_volatility": 0.01}
    
    print("\n--- Compliance Check 1 (EU): Compliant FX Trade (low leverage) ---")
    compliance_check1 = compliance_engine.check_compliance(mock_trade_prop1_low_leverage, mock_context1)
    print(f"Trade 1 ({mock_trade_prop1_low_leverage['symbol']} {mock_trade_prop1_low_leverage['action']}): Status={compliance_check1['status'].value}")
    for vio in compliance_check1['violations']: print(f"  - {vio['severity'].upper()}: {vio['message']}")

    print("\n--- Compliance Check 2 (EU): Non-compliant FX Trade (high implied leverage) ---")
    mock_trade_prop2_high_leverage = {
        "symbol": "EURUSD", "action": "BUY", "volume": 5.0, "entry_price": 1.0850,
        "stop_loss": 1.0800, "take_profit": 1.0900, "reasoning": "Test", "confidence": 0.8,
        "risk_assessment": {}
    }
    compliance_check2 = compliance_engine.check_compliance(mock_trade_prop2_high_leverage, mock_context1)
    print(f"Trade 2 ({mock_trade_prop2_high_leverage['symbol']} {mock_trade_prop2_high_leverage['action']}): Status={compliance_check2['status'].value}")
    for vio in compliance_check2['violations']: print(f"  - {vio['severity'].upper()}: {vio['message']}")


    # --- Test US-SEC Profile ---
    print("\n\n--- Testing US-SEC Compliance Profile ---")
    compliance_engine.set_jurisdiction_profile("US-SEC")

    print("\n--- Compliance Check 3 (US-SEC): Restricted Crypto Trade ---")
    mock_trade_prop3_crypto = {
        "symbol": "BTCUSD", "action": "SELL", "volume": 0.01, "entry_price": 30000.0,
        "stop_loss": 31000.0, "take_profit": 29000.0, "reasoning": "Test Crypto", "confidence": 0.9,
        "risk_assessment": {},
    }
    mock_context3 = {"account_equity": 50000.0, "current_market_volatility": 0.005}
    compliance_check3 = compliance_engine.check_compliance(mock_trade_prop3_crypto, mock_context3)
    print(f"Trade 3 ({mock_trade_prop3_crypto['symbol']} {mock_trade_prop3_crypto['action']}): Status={compliance_check3['status'].value}")
    for vio in compliance_check3['violations']: print(f"  - {vio['severity'].upper()}: {vio['message']}")

    print("\n--- Compliance Check 4 (US-SEC): Universal Warning Rule (High Volatility) ---")
    mock_trade_prop4_vol = {
        "symbol": "SPY", "action": "BUY", "volume": 10.0, "entry_price": 500.0,
        "reasoning": "Test Warning", "confidence": 0.7, "risk_assessment": {}
    }
    mock_context4 = {"account_equity": 100000.0, "current_market_volatility": 0.06} # High volatility
    compliance_check4 = compliance_engine.check_compliance(mock_trade_prop4_vol, mock_context4)
    print(f"Trade 4 ({mock_trade_prop4_vol['symbol']} {mock_trade_prop4_vol['action']}): Status={compliance_check4['status'].value}")
    for vio in compliance_check4['violations']: print(f"  - {vio['severity'].upper()}: {vio['message']}")
    
    # Clean up mock file
    if os.path.exists(compliance_rules_path):
        os.remove(compliance_rules_path)
        logger.info(f"Cleaned up mock compliance rules file: {compliance_rules_path}")