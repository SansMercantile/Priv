# backend/ai_core/subatomic_analysis.py

import logging
import random
import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# This file provides a functional, albeit simplified, engine for the AGI persona INPU
# to simulate the analysis and formation of matter at a sub-atomic and molecular level.
# This version includes logic for predicting molecular properties based on environment.

logger = logging.getLogger(__name__)

class Particle(BaseModel):
    """Represents a fundamental or composite particle."""
    name: str = Field(..., description="Name of the particle (e.g., 'Electron', 'Proton').")
    charge: float = Field(..., description="Electric charge of the particle.")
    mass: float = Field(..., description="Mass of the particle in atomic mass units (amu).")
    spin: float = Field(..., description="Spin of the particle.")

class Atom(BaseModel):
    """Represents a single atom of an element."""
    element: str = Field(..., description="The chemical element (e.g., 'Hydrogen', 'Carbon').")
    atomic_number: int = Field(..., description="The number of protons in the nucleus.")
    mass_number: int = Field(..., description="The total number of protons and neutrons.")
    electron_shell_configuration: Dict[int, int] = Field(..., description="Configuration of electrons in shells.")
    electronegativity: float = Field(..., description="A measure of the tendency of an atom to attract a bonding pair of electrons.")
    
    def valence_electrons(self) -> int:
        """Calculates the number of valence electrons."""
        if not self.electron_shell_configuration:
            return 0
        max_shell = max(self.electron_shell_configuration.keys())
        return self.electron_shell_configuration[max_shell]

class Molecule(BaseModel):
    """Represents a molecule composed of multiple atoms."""
    chemical_formula: str = Field(..., description="The chemical formula of the molecule (e.g., 'H2O').")
    atoms: List[Atom] = Field(..., description="A list of atoms that make up the molecule.")
    bonds: List[Dict[str, Any]] = Field(..., description="A functional list of bonds between atoms.")
    is_polar: bool = Field(..., description="Indicates if the molecule has a net dipole moment.")

    def get_molecular_state(self, temperature_kelvin: float, pressure_pa: float) -> str:
        """
        Predicts the state of matter (solid, liquid, gas) based on environmental conditions.
        This is a simplified model using common boiling/freezing points.
        """
        # Simplified model for water (H2O)
        if self.chemical_formula == "H2O":
            # Pressure adjustments to boiling point are complex; this is a basic model.
            boiling_point_k = 373.15 * (1 - (pressure_pa / 101325.0) * 0.05) # Rough approximation
            freezing_point_k = 273.15

            if temperature_kelvin <= freezing_point_k:
                return "Solid (Ice)"
            elif temperature_kelvin >= boiling_point_k:
                return "Gas (Vapor)"
            else:
                return "Liquid"
        return "Unknown"


class SubatomicAnalysisEngine:
    """
    A functional engine for INPU and PRIV to analyze and simulate matter.
    This implementation includes logic for chemical bond formation and property prediction.
    """
    def __init__(self):
        logger.info("Sub-Atomic Analysis Engine initialized (Functional).")
        self.known_elements = {
            1: {"name": "Hydrogen", "shells": {1: 1}, "electronegativity": 2.20},
            6: {"name": "Carbon", "shells": {1: 2, 2: 4}, "electronegativity": 2.55},
            8: {"name": "Oxygen", "shells": {1: 2, 2: 6}, "electronegativity": 3.44},
        }

    def create_atom(self, atomic_number: int) -> Optional[Atom]:
        """Creates an Atom object from its atomic number."""
        element_data = self.known_elements.get(atomic_number)
        if not element_data:
            return None
        return Atom(
            element=element_data["name"],
            atomic_number=atomic_number,
            mass_number=atomic_number * 2,
            electron_shell_configuration=element_data["shells"],
            electronegativity=element_data["electronegativity"]
        )

    def simulate_bond_formation(self, atom1: Atom, atom2: Atom) -> Optional[str]:
        """
        Simulates the formation of a chemical bond between two atoms.
        Returns the type of bond formed or None if no bond is likely.
        """
        electronegativity_diff = abs(atom1.electronegativity - atom2.electronegativity)
        if electronegativity_diff > 1.7:
            return "ionic"
        elif electronegativity_diff > 0.4:
            return "polar_covalent"
        elif electronegativity_diff >= 0:
            return "nonpolar_covalent"
        return None

    def analyze_molecular_composition(self, components: List[str]) -> List[Molecule]:
        """
        Analyzes a list of elements and simulates their molecular composition.
        """
        logger.info(f"Simulating molecular composition for components: {components}")
        atoms = [self.create_atom(self._element_to_num(c)) for c in components if self._element_to_num(c)]
        
        if len(atoms) < 2:
            return []

        if sorted(components) == sorted(["Hydrogen", "Hydrogen", "Oxygen"]):
            h1, h2, o = atoms[0], atoms[1], atoms[2]
            bond1 = self.simulate_bond_formation(o, h1)
            bond2 = self.simulate_bond_formation(o, h2)
            if bond1 and bond2:
                water_molecule = Molecule(
                    chemical_formula="H2O",
                    atoms=[h1, h2, o],
                    bonds=[
                        {"type": bond1, "from": o.element, "to": h1.element},
                        {"type": bond2, "from": o.element, "to": h2.element}
                    ],
                    is_polar=(bond1 == "polar_covalent") # Simplified polarity check
                )
                logger.info("Successfully simulated the formation of a water molecule.")
                return [water_molecule]
        
        return []

    def _element_to_num(self, name: str) -> Optional[int]:
        for num, data in self.known_elements.items():
            if data["name"].lower() == name.lower():
                return num
        return None
