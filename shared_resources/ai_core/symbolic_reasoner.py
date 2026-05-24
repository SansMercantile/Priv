# backend/ai_core/symbolic_reasoner.py

from typing import Dict, Any, List
from shared_resources.ai_core.knowledge_graph import KnowledgeGraph
from shared_resources.ai_core.rule_engine import RuleEngine
from shared_resources.ai_core.neural_encoder import NeuralEncoder

class SymbolicReasoner:
    """
    The high-level reasoning component of the AI core.
    It combines structured data from the Knowledge Graph with the logic from the Rule Engine
    and the semantic understanding from the Neural Encoder to form conclusions, generate hypotheses,
    and provide explainable insights.
    """
    def __init__(self, knowledge_graph: KnowledgeGraph, rule_engine: RuleEngine, neural_encoder: NeuralEncoder):
        """
        Initializes the Symbolic Reasoner with its necessary components.
        
        Args:
            knowledge_graph (KnowledgeGraph): An instance of the knowledge graph.
            rule_engine (RuleEngine): An instance of the rule engine.
            neural_encoder (NeuralEncoder): An instance of the neural encoder.
        """
        self.kg = knowledge_graph
        self.rule_engine = rule_engine
        self.encoder = neural_encoder
        print("Symbolic Reasoner initialized and linked to KG, Rule Engine, and Neural Encoder.")

    def generate_insight(self, primary_entity_id: str, market_facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a detailed insight for a primary entity by combining graph queries and rule evaluation.
        
        Args:
            primary_entity_id (str): The main entity to analyze (e.g., 'AAPL').
            market_facts (Dict[str, Any]): Current market data and facts.
            
        Returns:
            Dict[str, Any]: A dictionary containing the generated insight, evidence, and recommended actions.
        """
        
        # 1. Gather evidence from the Knowledge Graph
        relationships = self.kg.query_relationships(primary_entity_id, depth=1)
        
        # 2. Evaluate the current market facts with the Rule Engine
        triggered_actions = self.rule_engine.evaluate(market_facts)
        
        # 3. Synthesize the findings into a narrative
        insight_summary = f"Analysis for {primary_entity_id}: "
        evidence = []
        
        if relationships:
            insight_summary += "Key relationships identified. "
            evidence.append(f"Direct relationships: {relationships}")
        else:
            insight_summary += "No direct relationships found in the knowledge graph. "

        if triggered_actions:
            insight_summary += f"{len(triggered_actions)} rule(s) triggered, suggesting specific actions. "
            evidence.append(f"Triggered rule actions: {triggered_actions}")
        else:
            insight_summary += "No specific rules were triggered by current market facts. "
            
        # 4. Use Neural Encoder to find related concepts (conceptual search)
        try:
            primary_embedding = self.encoder.encode_text(primary_entity_id)
            # In a real system, you would compare this against a vector database of all node embeddings
            related_concepts_simulation = ["market_volatility", "tech_sector_sentiment"]
            evidence.append(f"Semantically related concepts (simulated): {related_concepts_simulation}")
        except Exception as e:
            evidence.append(f"Could not perform semantic search: {e}")

        return {
            "summary": insight_summary.strip(),
            "evidence": evidence,
            "recommended_actions": triggered_actions
        }

# Example Usage:
if __name__ == '__main__':
    # 1. Initialize all components
    kg = KnowledgeGraph()
    rule_engine = RuleEngine()
    encoder = NeuralEncoder()

    # 2. Populate Knowledge Graph
    kg.add_node('AAPL', 'Company', {'name': 'Apple Inc.', 'sector': 'Technology'})
    kg.add_node('interest_rates', 'EconomicIndicator', {'name': 'Federal Funds Rate'})
    kg.add_edge('interest_rates', 'AAPL', 'affects', {'effect': 'negative on valuation'})

    # 3. Populate Rule Engine
    rule = {
        "name": "Tech Sector Rate Sensitivity",
        "conditions": {
            "all": [
                {"fact": "interest_rates_rising", "operator": "equal", "value": True},
                {"fact": "analyzed_sector", "operator": "equal", "value": "Technology"}
            ]
        },
        "actions": [
            {"action": "generate_alert", "params": {"level": "warning", "message": "Rising interest rates may negatively impact tech stock valuations."}}
        ]
    }
    rule_engine.add_rule(rule)

    # 4. Create the Reasoner
    reasoner = SymbolicReasoner(knowledge_graph=kg, rule_engine=rule_engine, neural_encoder=encoder)

    # 5. Define current market facts
    current_facts = {
        "interest_rates_rising": True,
        "analyzed_sector": "Technology",
        "vix_index": 25 # This fact is present but won't trigger our specific rule
    }

    # 6. Generate an insight
    insight = reasoner.generate_insight('AAPL', current_facts)
    
    # 7. Print the result
    import json
    print("\n--- Generated Insight ---")
    print(json.dumps(insight, indent=2))
