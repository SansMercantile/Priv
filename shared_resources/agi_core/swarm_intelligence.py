# shared_resources/agi_core/swarm_intelligence.py

import random
from typing import List, Dict, Any

class SwarmAgent:
    """
    A simple agent that follows a basic set of rules.
    The collective behavior of many such agents can lead to emergent intelligence.
    """
    def __init__(self, agent_id: int):
        self.id = agent_id
        self.position: float = random.uniform(-1, 1)  # Represents a position on a spectrum (e.g., bearish to bullish)
        self.velocity: float = 0.0
        self.personal_best_position: float = self.position
        self.personal_best_score: float = -float('inf')

    def update_position(self, global_best_position: float, inertia: float, cognitive_weight: float, social_weight: float):
        """
        Update agent's velocity and position based on personal and global bests.
        This is a core concept of Particle Swarm Optimization (PSO).

        Args:
            global_best_position (float): The best position found by any agent in the swarm.
            inertia (float): How much of the previous velocity is retained.
            cognitive_weight (float): How much the agent is attracted to its personal best.
            social_weight (float): How much the agent is attracted to the swarm's best.
        """
        r1 = random.random()
        r2 = random.random()

        cognitive_velocity = cognitive_weight * r1 * (self.personal_best_position - self.position)
        social_velocity = social_weight * r2 * (global_best_position - self.position)
        
        self.velocity = (inertia * self.velocity) + cognitive_velocity + social_velocity
        self.position += self.velocity
        
        # Clamp position to a valid range, e.g., [-1, 1]
        self.position = max(-1, min(1, self.position))

    def evaluate_fitness(self, objective_function):
        """
        Evaluates the fitness of the agent's current position.
        
        Args:
            objective_function (function): A function that takes a position and returns a score.
        """
        score = objective_function(self.position)
        if score > self.personal_best_score:
            self.personal_best_score = score
            self.personal_best_position = self.position

class SwarmIntelligence:
    """
    Manages a swarm of simple agents to find optimal solutions to complex problems.
    This can be used for tasks like optimizing strategy parameters or finding market consensus.
    """
    def __init__(self, num_agents: int, inertia: float = 0.5, cognitive_weight: float = 0.8, social_weight: float = 0.9):
        self.swarm: List[SwarmAgent] = [SwarmAgent(i) for i in range(num_agents)]
        self.global_best_position: float = 0.0
        self.global_best_score: float = -float('inf')
        self.inertia = inertia
        self.cognitive_weight = cognitive_weight
        self.social_weight = social_weight
        print(f"SwarmIntelligence initialized with {num_agents} agents.")

    def run_iteration(self, objective_function):
        """
        Runs a single iteration of the swarm optimization.

        Args:
            objective_function (function): The function the swarm is trying to optimize.
        """
        for agent in self.swarm:
            agent.evaluate_fitness(objective_function)
            if agent.personal_best_score > self.global_best_score:
                self.global_best_score = agent.personal_best_score
                self.global_best_position = agent.personal_best_position
        
        for agent in self.swarm:
            agent.update_position(self.global_best_position, self.inertia, self.cognitive_weight, self.social_weight)

# Example Usage:
if __name__ == '__main__':
    # Define an objective function we want to optimize.
    # Let's say we're trying to find the market sentiment on a scale of -1 (bearish) to 1 (bullish).
    # The true sentiment is 0.75, and the closer an agent gets, the higher its score.
    def get_market_sentiment_score(position: float) -> float:
        true_sentiment = 0.75
        # The score is higher the closer the position is to the true sentiment.
        return 1.0 - abs(true_sentiment - position)

    swarm = SwarmIntelligence(num_agents=20)
    
    print("\n--- Running Swarm Optimization to find Market Consensus ---")
    for i in range(15):
        swarm.run_iteration(get_market_sentiment_score)
        print(f"Iteration {i+1}: Best consensus found at {swarm.global_best_position:.4f} (Score: {swarm.global_best_score:.4f})")

    print("\n--- Optimization Complete ---")
    print(f"Final swarm consensus for market sentiment: {swarm.global_best_position:.4f}")
