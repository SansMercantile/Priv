# shared_resources/agi_core/collective_decision_engine.py

from typing import List, Dict, Any, Callable
from collections import Counter

class CollectiveDecisionEngine:
    """
    An engine that facilitates collective decision-making among a group of agents.
    It aggregates opinions, proposals, or votes to arrive at a single, consensus-driven action.
    """
    def __init__(self):
        print("CollectiveDecisionEngine initialized.")

    def make_decision(self, proposals: List[Dict[str, Any]], method: str = 'weighted_vote') -> Dict[str, Any]:
        """
        Makes a final decision based on a list of proposals from various agents.

        Args:
            proposals (List[Dict[str, Any]]): A list of proposed actions. Each proposal
                                              should be a dictionary containing at least 'action'
                                              and 'confidence' keys.
            method (str): The method to use for decision-making ('simple_majority', 'weighted_vote').

        Returns:
            Dict[str, Any]: The winning proposal.
        """
        if not proposals:
            return {"action": "HOLD", "reason": "No proposals submitted.", "confidence": 1.0}

        if method == 'simple_majority':
            return self._simple_majority_vote(proposals)
        elif method == 'weighted_vote':
            return self._weighted_vote(proposals)
        else:
            raise ValueError(f"Unsupported decision method: {method}")

    def _simple_majority_vote(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        The action with the most votes wins. Confidence is averaged.
        """
        print("\n--- Making decision via Simple Majority ---")
        if not proposals: return {}
        
        action_votes = [p['action'] for p in proposals]
        vote_counts = Counter(action_votes)
        winning_action = vote_counts.most_common(1)[0][0]
        
        # Find the original proposals that match the winning action
        winning_proposals = [p for p in proposals if p['action'] == winning_action]
        
        # Average the confidence of the winning proposals
        avg_confidence = sum(p['confidence'] for p in winning_proposals) / len(winning_proposals)
        
        result = winning_proposals[0].copy() # Use first proposal as a template
        result['confidence'] = avg_confidence
        result['reason'] = f"Consensus by simple majority ({vote_counts[winning_action]} votes)."
        
        print(f"Winning action: '{winning_action}' with average confidence {avg_confidence:.2f}")
        return result

    def _weighted_vote(self, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Each action's vote is weighted by the confidence of its proposal.
        """
        print("\n--- Making decision via Weighted Vote ---")
        if not proposals: return {}

        weighted_scores: Dict[str, float] = {}
        proposal_map: Dict[str, Dict[str, Any]] = {}

        for p in proposals:
            action = p['action']
            confidence = p.get('confidence', 0.5)
            
            if action not in weighted_scores:
                weighted_scores[action] = 0
                proposal_map[action] = p # Store the first proposal for this action
            
            weighted_scores[action] += confidence
        
        # Find the action with the highest total weighted score
        winning_action = max(weighted_scores, key=weighted_scores.get)
        
        result = proposal_map[winning_action].copy()
        result['confidence'] = weighted_scores[winning_action] / sum(1 for p in proposals if p['action'] == winning_action) # Avg confidence
        result['reason'] = f"Consensus by weighted vote (Total Score: {weighted_scores[winning_action]:.2f})."

        print(f"Winning action: '{winning_action}' with total weighted score {weighted_scores[winning_action]:.2f}")
        return result


# Example Usage:
if __name__ == '__main__':
    decision_engine = CollectiveDecisionEngine()

    # Simulate proposals from different agents for the same asset
    agent_proposals = [
        {'agent': 'QuantitativeAgent', 'action': 'BUY', 'symbol': 'AAPL', 'confidence': 0.85},
        {'agent': 'TechnicalAgent', 'action': 'BUY', 'symbol': 'AAPL', 'confidence': 0.70},
        {'agent': 'SentimentAgent', 'action': 'HOLD', 'symbol': 'AAPL', 'confidence': 0.60},
        {'agent': 'RiskAgent', 'action': 'SELL', 'symbol': 'AAPL', 'confidence': 0.95, 'reason': 'High VaR'},
        {'agent': 'FundamentalAgent', 'action': 'BUY', 'symbol': 'AAPL', 'confidence': 0.75},
    ]

    # --- Run Decision-Making ---
    final_decision_weighted = decision_engine.make_decision(agent_proposals, method='weighted_vote')
    print(f"Final Decision (Weighted): {final_decision_weighted}")
    
    final_decision_majority = decision_engine.make_decision(agent_proposals, method='simple_majority')
    print(f"Final Decision (Majority): {final_decision_majority}")
