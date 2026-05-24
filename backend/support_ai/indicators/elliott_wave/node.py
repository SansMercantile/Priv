# backend/support_ai/indicators/elliott_wave/node.py

from __future__ import annotations
from typing import List, Optional
from .wave import Wave

class Node:
    """
    Represents a node in the wave analysis tree. Each node can contain a wave
    and have multiple child nodes representing sub-waves.
    """
    def __init__(self, text: str, wave: Optional[Wave] = None, parent: Optional[Node] = None):
        self.childs: List[Node] = []
        self.wave: Optional[Wave] = wave
        self.text: str = text
        self.parent: Optional[Node] = parent
        self.selected: bool = False

    def add(self, text: str, wave: Optional[Wave] = None) -> Node:
        """Adds a new child node to this node."""
        node = Node(text, wave, self)
        self.childs.append(node)
        return node

    def clear(self):
        """Recursively clears all child nodes and associated wave data."""
        for child in self.childs:
            child.clear()
        self.childs.clear()
        self.wave = None

