import logging
import json
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime # <--- THIS IMPORT WAS ADDED

logger = logging.getLogger(__name__)

# --- Enums for Policy Directives ---
class PolicyType(str, Enum):
    RISK_ADJUSTMENT = "risk_adjustment"
    STRATEGY_FOCUS = "strategy_focus"
    COMPLIANCE_AMENDMENT = "compliance_amendment"
    ETHICAL_OVERRIDE = "ethical_override"
    RESOURCE_ALLOCATION = "resource_allocation" # For multi-agent scaling
    OTHER = "other"

class PolicySeverity(str, Enum):
    CRITICAL_OVERRIDE = "critical_override" # Must apply immediately, hard override
    HIGH_IMPACT = "high_impact"           # Strong recommendation, prioritize
    GUIDANCE = "guidance"                 # Soft recommendation, inform AI
    ADVISORY = "advisory"                 # For human consumption/review

# --- Pydantic Models for Policy Definitions ---
class PolicyDirective(BaseModel):
    """
    Defines a high-level policy directive from human governance.
    """
    policy_id: str = Field(..., description="Unique ID for the policy.")
    name: str = Field(..., description="Name of the policy.")
    description: str = Field(..., description="Detailed description of the policy.")
    policy_type: PolicyType = Field(..., description="Category of the policy.")
    severity: PolicySeverity = Field(PolicySeverity.GUIDANCE, description="Severity of the policy application.")
    target_agents: List[str] = Field(default_factory=list, description="Specific agents this policy targets (e.g., ['Priv_Main_Strategist', 'SOLVA_CFO']). Empty means all relevant.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters that the compiler translates into AI-consumable settings.")
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(None)


class PolicyCompiler:
    """
    Translates high-level human governance directives into AI-consumable protocols.
    This is Priv's Policy-aware Instruction Compiler.
    """
    def __init__(self, policy_definitions_path: str = "backend/governance/policies.json"):
        self.policy_definitions_path = policy_definitions_path
        self.active_policies: Dict[str, PolicyDirective] = {} # policy_id -> PolicyDirective
        self._load_policy_definitions()
        logger.info("Priv's PolicyCompiler initialized.")

    def _load_policy_definitions(self):
        """Loads policy directives from a JSON file."""
        if not os.path.exists(self.policy_definitions_path):
            logger.warning(f"Priv: Policy definitions file not found at {self.policy_definitions_path}. No policies loaded.")
            return

        try:
            with open(self.policy_definitions_path, "r", encoding="utf-8") as f:
                raw_policies = json.load(f)
                for policy_data in raw_policies:
                    try:
                        policy_def = PolicyDirective(**policy_data)
                        self.active_policies[policy_def.policy_id] = policy_def
                    except Exception as e:
                        logger.error(f"Priv: Error parsing policy definition {policy_data.get('policy_id', 'Unknown')}: {e}")
            logger.info(f"Priv: Loaded {len(self.active_policies)} policy definitions.")
        except Exception as e:
            logger.error(f"Priv: Error loading policy definitions from {self.policy_definitions_path}: {e}", exc_info=True)
            self.active_policies = {}

    def get_active_policies_for_agent(self, agent_id: str) -> List[PolicyDirective]:
        """
        Retrieves all active policies relevant to a specific Priv agent.
        """
        relevant_policies = []
        now = datetime.now()
        for policy_id, policy_obj in self.active_policies.items():
            if (policy_obj.expires_at is None or policy_obj.expires_at > now) and \
               (not policy_obj.target_agents or agent_id in policy_obj.target_agents):
                relevant_policies.append(policy_obj)
        return relevant_policies

    def compile_directives_for_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Compiles relevant high-level policies into a set of actionable, AI-consumable settings
        for a given Priv agent.

        Returns:
            Dict[str, Any]: A dictionary of compiled settings (e.g., {'risk_multiplier': 0.8, 'strategy_bias': 'conservative'}).
        """
        compiled_settings = {}
        relevant_policies = self.get_active_policies_for_agent(agent_id)

        for policy in relevant_policies:
            logger.debug(f"Priv: Compiling policy '{policy.name}' for agent '{agent_id}'.")
            
            if policy.policy_type == PolicyType.RISK_ADJUSTMENT:
                if policy.parameters.get("adjust_risk_by_percent"):
                    adjustment_factor = 1 - (policy.parameters["adjust_risk_by_percent"] / 100.0)
                    compiled_settings['risk_multiplier'] = compiled_settings.get('risk_multiplier', 1.0) * adjustment_factor
                    logger.info(f"Priv: Policy '{policy.name}' adjusted risk multiplier for '{agent_id}' to {compiled_settings['risk_multiplier']:.2f}.")
            
            elif policy.policy_type == PolicyType.STRATEGY_FOCUS:
                if policy.parameters.get("focus_on_volatility_breakouts"):
                    compiled_settings['strategy_bias_volatility_breakouts'] = True
                    logger.info(f"Priv: Policy '{policy.name}' set strategy bias for '{agent_id}' to volatility breakouts.")

            elif policy.policy_type == PolicyType.COMPLIANCE_AMENDMENT:
                if "new_jurisdiction_profile" in policy.parameters:
                    compiled_settings['set_jurisdiction_profile'] = policy.parameters["new_jurisdiction_profile"]
                    logger.info(f"Priv: Policy '{policy.name}' suggests new jurisdiction profile: {policy.parameters['new_jurisdiction_profile']}.")

            elif policy.policy_type == PolicyType.ETHICAL_OVERRIDE:
                if "override_principle_id" in policy.parameters and "new_severity" in policy.parameters:
                    compiled_settings['ethical_override_request'] = {
                        "principle_id": policy.parameters["override_principle_id"],
                        "new_severity": policy.parameters["new_severity"]
                    }
                    logger.warning(f"Priv: Policy '{policy.name}' requests ethical principle override for '{policy.parameters['override_principle_id']}' to '{policy.parameters['new_severity']}'.")
            
        logger.info(f"Priv: Policy compilation for agent '{agent_id}' complete. Compiled settings: {compiled_settings}.")
        return compiled_settings

# Example Usage:
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    mock_policies_content = [
        {
            "policy_id": "GLOBAL_RISK_REDUCTION_Q3",
            "name": "Q3 Risk Reduction Mandate",
            "description": "Reduce overall portfolio risk by 20% due to upcoming macroeconomic uncertainty.",
            "policy_type": "risk_adjustment",
            "severity": "critical_override",
            "target_agents": ["Priv_Main_Strategist", "SOLVA_CFO"],
            "parameters": {"adjust_risk_by_percent": 20},
            "created_at": "2025-07-01T00:00:00",
            "expires_at": "2025-09-30T23:59:59"
        },
        {
            "policy_id": "NEW_JURISDICTION_AU",
            "name": "Australian Regulatory Compliance",
            "description": "Activate Australian regulatory profile for AUD pairs.",
            "policy_type": "compliance_amendment",
            "severity": "high_impact",
            "target_agents": [],
            "parameters": {"new_jurisdiction_profile": "AU-ASIC"},
            "created_at": "2025-07-05T00:00:00"
        },
        {
            "policy_id": "ETHICS_NO_FRACKING_STOCKS",
            "name": "Ethical Sourcing: No Fracking Stocks",
            "description": "Ethical stance to avoid investments in companies involved in fracking operations.",
            "policy_type": "ethical_override",
            "severity": "critical_override",
            "target_agents": ["SOLVA_CFO"],
            "parameters": {"override_principle_id": "P_ESG_NO_FOSSIL_FUELS", "new_severity": "critical"}
        }
    ]
    policies_path = "backend/governance/policies.json"
    os.makedirs(os.path.dirname(policies_path), exist_ok=True)
    with open(policies_path, "w", encoding="utf-8") as f:
        json.dump(mock_policies_content, f, indent=2, default=str)
    logger.info(f"Mock policy definitions saved to {policies_path}")

    policy_compiler = PolicyCompiler(policy_definitions_path=policies_path)

    print("\n--- Compiling Policies for Priv_Main_Strategist ---")
    agent_id_main = "Priv_Main_Strategist"
    compiled_directives_main = policy_compiler.compile_directives_for_agent(agent_id_main)
    print(f"Compiled Directives for '{agent_id_main}':\n{json.dumps(compiled_directives_main, indent=2)}")

    print("\n--- Compiling Policies for SOLVA_CFO ---")
    agent_id_solva = "SOLVA_CFO"
    compiled_directives_solva = policy_compiler.compile_directives_for_agent(agent_id_solva)
    print(f"Compiled Directives for '{agent_id_solva}':\n{json.dumps(compiled_directives_solva, indent=2)}")

    print("\n--- Compiling Policies for Priv_Departmental_Agent ---")
    agent_id_dept = "Priv_Departmental_Agent"
    compiled_directives_dept = policy_compiler.compile_directives_for_agent(agent_id_dept)
    print(f"Compiled Directives for '{agent_id_dept}':\n{json.dumps(compiled_directives_dept, indent=2)}")

    if os.path.exists(policies_path):
        os.remove(policies_path)
        logger.info(f"Cleaned up mock policy definitions file: {policies_path}")