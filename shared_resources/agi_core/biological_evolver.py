# shared_resources/agi_core/biological_evolver.py

import random
from dataclasses import dataclass, field
from typing import List, Dict, Any
import logging

# It's better practice to import the specific classes you need.
from shared_resources.agi_core.terraforming_simulator import Atmosphere, Geology, Hydrology

logger = logging.getLogger(__name__)

@dataclass
class Organism:
    """Represents a single biological entity with a set of genetic traits."""
    name: str
    generation: int = 1
    dna: str = ""
    fitness: float = 0.0 # A score of how well it's adapted to the environment
    
    # Genetic traits derived from DNA
    traits: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """If no DNA is provided, generate a random one."""
        if not self.dna:
            self.dna = ''.join(random.choices('ATCG', k=100))
        self.express_traits()
        
    def express_traits(self):
        """Translate DNA into functional traits."""
        # This is a simplified model. A real one would be far more complex.
        self.traits['temperature_tolerance'] = self.dna.count('A') / 2.0  # Celsius range
        self.traits['radiation_resistance'] = self.dna.count('T') / 100.0
        self.traits['oxygen_requirement'] = self.dna.count('C') / 100.0
        self.traits['toxicity_resistance'] = self.dna.count('G') / 100.0
        
    def calculate_fitness(self, atmosphere: Atmosphere, geology: Geology, hydrology: Hydrology):
        """
        Calculates the organism's fitness based on environmental conditions.
        
        Args:
            atmosphere (Atmosphere): The current planetary atmosphere.
            geology (Geology): The current planetary geology.
            hydrology (Hydrology): The current planetary hydrology.
        """
        score = 1.0
        # Temperature fitness
        temp_diff = abs(atmosphere.temperature_celsius - 15) # Optimal is 15C
        if self.traits['temperature_tolerance'] > 0:
            score *= max(0, 1 - (temp_diff / self.traits['temperature_tolerance']))
        else:
            score = 0
        
        # Oxygen fitness
        oxygen_diff = abs(atmosphere.composition.get('oxygen', 0) - 21)
        if score > 0: # a dead organism can't benefit from oxygen
            score *= max(0, 1 - (oxygen_diff * self.traits['oxygen_requirement']))
        
        self.fitness = score

class BiologicalEvolver:
    """
    Manages a population of organisms and evolves them over generations
    based on environmental pressures from a TerraformingSimulator.
    """
    def __init__(self, population_size: int = 100):
        self.population_size = population_size
        self.population: List[Organism] = [
            Organism(name=f"Org-{i}") for i in range(population_size)
        ]
        self.generation = 1
        logger.info(f"BiologicalEvolver initialized with population of {population_size}.")

    def assess_population_fitness(self, atmosphere: Atmosphere, geology: Geology, hydrology: Hydrology):
        """Calculates fitness for every organism in the population."""
        for org in self.population:
            org.calculate_fitness(atmosphere, geology, hydrology)
        
        # Sort population by fitness, highest first
        self.population.sort(key=lambda x: x.fitness, reverse=True)

    def evolve_next_generation(self):
        """
        Creates the next generation through selection, crossover, and mutation.
        """
        logger.info(f"\nEvolving to generation {self.generation + 1}...")
        
        # Select the top 20% as parents for the next generation
        parent_pool = [org for org in self.population if org.fitness > 0][:self.population_size // 5]
        
        if not parent_pool:
            logger.warning("Extinction event! No organisms survived to reproduce.")
            self.population = []
            return

        next_generation: List[Organism] = []
        
        # Create new offspring
        while len(next_generation) < self.population_size:
            parent1 = random.choice(parent_pool)
            parent2 = random.choice(parent_pool)
            
            # Crossover
            crossover_point = random.randint(1, len(parent1.dna) - 1)
            child_dna = parent1.dna[:crossover_point] + parent2.dna[crossover_point:]
            
            # Mutation
            mutation_rate = 0.01 # 1% chance per gene
            mutated_dna_list = []
            for gene in child_dna:
                if random.random() < mutation_rate:
                    mutated_dna_list.append(random.choice('ATCG'))
                else:
                    mutated_dna_list.append(gene)
            mutated_dna = "".join(mutated_dna_list)
            
            child = Organism(
                name=f"Org-{len(next_generation)}",
                generation=self.generation + 1,
                dna=mutated_dna
            )
            next_generation.append(child)
            
        self.population = next_generation
        self.generation += 1
        logger.info(f"New generation created. Population size: {len(self.population)}.")
        
    def get_fittest_organism(self) -> Organism:
        """Returns the most adapted organism in the current population."""
        return self.population[0] if self.population else None

# Example Usage:
if __name__ == '__main__':
    import asyncio
    
    # We need to define the TerraformingSimulator for the test to run.
    # This is a simplified version for demonstration purposes.
    from dataclasses import dataclass, field

    @dataclass
    class Atmosphere:
        composition: Dict[str, float] = field(default_factory=dict)
        temperature_celsius: float = 15.0

    @dataclass
    class Geology:
        """Geological properties of a planet"""
        tectonic_activity: float = 0.5  # 0-1 scale
        volcanic_activity: float = 0.3  # 0-1 scale
        seismic_stability: float = 0.7  # 0-1 scale
        mineral_composition: Dict[str, float] = None
        crust_thickness_km: float = 30.0
        core_temperature_k: float = 5000.0
        magnetic_field_strength: float = 0.5  # Relative to Earth
        
        def __post_init__(self):
            if self.mineral_composition is None:
                self.mineral_composition = {
                    'silicates': 0.6,
                    'iron': 0.2,
                    'water_ice': 0.1,
                    'other': 0.1
                }

    @dataclass
    class Hydrology:
        """Hydrological properties of a planet"""
        surface_water_coverage: float = 0.0  # 0-1 (0% to 100%)
        subsurface_water: bool = False
        ice_caps: bool = False
        ocean_depth_km: float = 0.0
        water_salinity: float = 0.0  # Parts per thousand
        precipitation_rate: float = 0.0  # mm/year
        evaporation_rate: float = 0.0  # mm/year
        groundwater_reserves: float = 0.0  # km³
        
        def get_water_cycle_balance(self) -> float:
            """Calculate water cycle balance"""
            return self.precipitation_rate - self.evaporation_rate

    class TerraformingSimulator:
        def __init__(self, name: str):
            self.planet_name = name
            self.atmosphere = Atmosphere()
            self.geology = Geology()
            self.hydrology = Hydrology()

    async def main():
        # Create a planetary environment
        planet = TerraformingSimulator("Test Planet")
        planet.atmosphere.temperature_celsius = 45 # A harsh environment
        
        # Create the evolver
        evolver = BiologicalEvolver(population_size=50)
        
        print("\n--- Evolution Simulation Start ---")
        
        for i in range(10):
            print(f"\n--- Generation {evolver.generation} ---")
            
            # Assess fitness against the planet's environment
            evolver.assess_population_fitness(planet.atmosphere, planet.geology, planet.hydrology)
            
            fittest = evolver.get_fittest_organism()
            if fittest:
                print(f"Fittest organism has fitness {fittest.fitness:.4f}")
                print(f"  -> Temp. Tolerance: {fittest.traits['temperature_tolerance']:.2f}°C")
            else:
                break
                
            # Evolve the next generation
            evolver.evolve_next_generation()
            
        print("\n--- Evolution Simulation End ---")

    asyncio.run(main())
