# shared_resources/agi_core/terraforming_simulator.py

from dataclasses import dataclass, field
from typing import Dict, List, Any
import random
import time
import logging

logger = logging.getLogger(__name__)

@dataclass
class Atmosphere:
    """Represents the atmospheric composition and conditions of a simulated planet."""
    composition: Dict[str, float] = field(default_factory=lambda: {
        'nitrogen': 78.0,
        'oxygen': 21.0,
        'argon': 0.9,
        'co2': 0.04,
    })
    pressure_hpa: float = 1013.25  # Hectopascals at sea level
    temperature_celsius: float = 15.0

@dataclass
class Geology:
    """Represents the geological makeup of a simulated planet."""
    tectonic_stability: float = 0.9  # 1.0 is perfectly stable
    volcanic_activity: float = 0.1   # 0.0 is inactive
    resource_distribution: Dict[str, float] = field(default_factory=lambda: {
        'iron': 0.5,
        'silicon': 0.28,
        'water_ice': 0.1,
        'rare_metals': 0.01,
    })

@dataclass
class Hydrology:
    """Represents the water systems of a simulated planet."""
    surface_water_coverage: float = 0.71  # Percentage of surface covered by liquid water
    ocean_salinity_ppt: float = 35.0      # Parts per thousand
    water_vapor_ppm: float = 3000.0       # Parts per million in atmosphere

class TerraformingSimulator:
    """
    A simulator for modeling the terraforming of a planetary environment.
    This class manages the state of the atmosphere, geology, and hydrology,
    and evolves them over time based on simulated events or AI interventions.
    """
    def __init__(self, planet_name: str):
        """
        Initializes the simulator with a new planet.
        
        Args:
            planet_name (str): The name of the simulated planet.
        """
        self.planet_name = planet_name
        self.simulation_time_years: float = 0.0
        self.atmosphere = Atmosphere()
        self.geology = Geology()
        self.hydrology = Hydrology()
        logger.info(f"Terraforming simulator for planet '{self.planet_name}' initialized.")

    def introduce_atmospheric_processor(self, gas_to_reduce: str, reduction_rate: float):
        """
        Simulates the deployment of a technology to alter the atmosphere.
        
        Args:
            gas_to_reduce (str): The gas to be reduced (e.g., 'co2').
            reduction_rate (float): The percentage reduction per year.
        """
        if gas_to_reduce in self.atmosphere.composition:
            logger.info(f"Deploying atmospheric processor to reduce {gas_to_reduce}.")
            # In a real simulation, this would be a persistent effect.
            # For this example, we apply it instantly for demonstration.
            current_level = self.atmosphere.composition[gas_to_reduce]
            self.atmosphere.composition[gas_to_reduce] *= (1 - reduction_rate)
            logger.info(f" -> {gas_to_reduce} reduced from {current_level:.4f}% to {self.atmosphere.composition[gas_to_reduce]:.4f}%.")
        else:
            logger.warning(f"Gas '{gas_to_reduce}' not found in atmosphere.")

    def simulate_meteor_impact(self, size_km: float):
        """
        Simulates a random meteor impact event.
        
        Args:
            size_km (float): The diameter of the impacting meteor in kilometers.
        """
        logger.info(f"EVENT: A meteor of {size_km}km diameter has impacted {self.planet_name}!")
        self.geology.tectonic_stability -= size_km * 0.01
        self.geology.volcanic_activity += size_km * 0.05
        dust_ejected = size_km * 1000
        self.hydrology.water_vapor_ppm += dust_ejected
        self.atmosphere.temperature_celsius -= size_km * 2.0 # Impact winter effect
        logger.info(" -> Geological stability and atmospheric conditions have been altered.")

    def advance_time(self, years: float):
        """
        Advances the simulation by a number of years, applying gradual changes.
        """
        logger.info(f"\nAdvancing simulation by {years} years...")
        # Simulate gradual atmospheric stabilization and temperature normalization
        self.atmosphere.temperature_celsius += 0.1 * years
        self.geology.volcanic_activity *= (0.95 ** years) # Activity slowly decays
        self.simulation_time_years += years
        logger.info(f"Simulation time: {self.simulation_time_years:.2f} years.")

    def get_planet_state(self) -> Dict[str, Any]:
        """Returns the current state of the planet."""
        return {
            "planet_name": self.planet_name,
            "simulation_time_years": self.simulation_time_years,
            "atmosphere": self.atmosphere,
            "geology": self.geology,
            "hydrology": self.hydrology,
        }

    def run_simulation_step(self, actions: Dict[str, Any]):
        """Runs a single step of the simulation based on terraforming actions."""
        logger.info(f"Running terraforming simulation step for {self.planet_name} with actions: {actions}")
        # Example simulation logic
        if "introduce_gas" in actions:
            gas, amount = actions["introduce_gas"]
            # This logic needs to be adapted for the new dataclass structure
            if gas in self.atmosphere.composition:
                 self.atmosphere.composition[gas] += amount
        if "increase_temperature" in actions:
            self.atmosphere.temperature_celsius += actions["increase_temperature"]

# Example Usage:
if __name__ == '__main__':
    import asyncio
    async def main():
        # Initialize a simulation for a hypothetical planet
        planet_x = TerraformingSimulator(planet_name="Kepler-186f")
        
        print("\n--- Initial Planet State ---")
        print(planet_x.get_planet_state())
        
        planet_x.advance_time(100)
        
        print("\n--- Simulating a Major Event ---")
        planet_x.simulate_meteor_impact(size_km=0.5)
        
        print("\n--- State After Impact ---")
        print(planet_x.get_planet_state())
        
        print("\n--- Deploying Terraforming Technology ---")
        planet_x.introduce_atmospheric_processor('co2', reduction_rate=0.1)
        
        planet_x.advance_time(500)
        
        print("\n--- Final Planet State ---")
        print(planet_x.get_planet_state())

    asyncio.run(main())

