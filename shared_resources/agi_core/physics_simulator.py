# shared_resources/agi_core/physics_simulator.py

from dataclasses import dataclass, field
from typing import List, Tuple, Dict
import numpy as np
import logging

logger = logging.getLogger(__name__)

@dataclass
class Particle:
    """Represents a fundamental particle in the simulation."""
    id: int
    mass: float
    charge: float
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    spin: float = 0.5

@dataclass
class QuantumField:
    """Represents a quantum field that permeates the simulation space."""
    name: str
    excitation_energy: float # Energy required to create a particle
    value: np.ndarray # Value of the field at every point in space (simplified)

class PhysicsSimulator:
    """
    A simplified physics engine to model interactions between particles and fields.
    This can be used by the AGI to test hypotheses about fundamental relationships
    in a controlled, simulated universe.
    """
    def __init__(self, space_dimensions: Tuple[int, int, int] = (100, 100, 100)):
        """
        Initializes the physics simulator.
        
        Args:
            space_dimensions (Tuple[int, int, int]): The size of the simulated space.
        """
        self.space_dimensions = space_dimensions
        self.particles: List[Particle] = []
        self.fields: Dict[str, QuantumField] = {}
        self.time_step: float = 0.01  # Simulation time step in seconds
        self.gravity_constant: float = 6.674e-11
        logger.info(f"PhysicsSimulator initialized with space of size {space_dimensions}.")

    def add_particle(self, mass: float, charge: float, position: List[float], velocity: List[float]) -> Particle:
        """Adds a new particle to the simulation."""
        p_id = len(self.particles)
        particle = Particle(
            id=p_id,
            mass=mass,
            charge=charge,
            position=np.array(position, dtype=float),
            velocity=np.array(velocity, dtype=float)
        )
        self.particles.append(particle)
        logger.info(f"Added Particle {p_id} at position {position}.")
        return particle

    def add_field(self, name: str, excitation_energy: float):
        """Adds a new quantum field to the simulation."""
        field_values = np.zeros(self.space_dimensions)
        q_field = QuantumField(name=name, excitation_energy=excitation_energy, value=field_values)
        self.fields[name] = q_field
        logger.info(f"Added QuantumField '{name}'.")

    def update(self):
        """
        Advances the simulation by one time step.
        Calculates forces and updates particle positions and velocities.
        """
        forces = [np.zeros(3) for _ in self.particles]

        # Calculate gravitational forces (simplified N-body simulation)
        for i, p1 in enumerate(self.particles):
            for j, p2 in enumerate(self.particles):
                if i == j:
                    continue
                
                direction_vector = p2.position - p1.position
                distance_sq = np.sum(direction_vector**2)
                
                if distance_sq < 1e-6: # Avoid division by zero
                    continue
                    
                force_magnitude = self.gravity_constant * p1.mass * p2.mass / distance_sq
                force_vector = force_magnitude * direction_vector / np.sqrt(distance_sq)
                forces[i] += force_vector
        
        # Update positions and velocities
        for i, particle in enumerate(self.particles):
            # Avoid division by zero for massless particles
            if particle.mass == 0:
                continue
            acceleration = forces[i] / particle.mass
            particle.velocity += acceleration * self.time_step
            particle.position += particle.velocity * self.time_step

# Example Usage:
if __name__ == '__main__':
    import asyncio

    async def main():
        simulator = PhysicsSimulator()
        
        print("\n--- Setting up simulation ---")
        # Add a central, heavy "star"
        simulator.add_particle(mass=1.989e6, charge=0, position=[50, 50, 50], velocity=[0, 0, 0])
        # Add a lighter "planet" in orbit
        simulator.add_particle(mass=5.972e3, charge=0, position=[70, 50, 50], velocity=[0, 10, 0])
        
        print("\n--- Running simulation for 1000 steps ---")
        for step in range(1000):
            simulator.update()
            if step % 100 == 0:
                planet = simulator.particles[1]
                print(f"Step {step}: Planet position = {np.round(planet.position, 2)}")
                
        print("\n--- Simulation complete ---")
        final_pos = np.round(simulator.particles[1].position, 2)
        print(f"Final planet position: {final_pos}")

    asyncio.run(main())
