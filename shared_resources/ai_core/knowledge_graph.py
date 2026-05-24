# backend/ai_core/knowledge_graph.py

import networkx as nx
from typing import List, Dict, Any, Tuple

class KnowledgeGraph:
    """
    Manages a graph database of financial entities, concepts, and their relationships.
    This allows the AI to understand the connections between different pieces of information,
    such as how a specific economic event might affect a particular company's stock price.
    """
    def __init__(self):
        """Initializes the knowledge graph."""
        self.graph = nx.MultiDiGraph()
        print("Knowledge Graph initialized.")

    def add_node(self, node_id: str, node_type: str, properties: Dict[str, Any]):
        """
        Adds a node (entity or concept) to the knowledge graph.
        
        Args:
            node_id (str): The unique identifier for the node (e.g., 'AAPL', 'Jerome Powell').
            node_type (str): The type of the node (e.g., 'Company', 'Person', 'EconomicIndicator').
            properties (Dict[str, Any]): A dictionary of attributes for the node.
        """
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, type=node_type, **properties)
            # print(f"Added node '{node_id}' of type '{node_type}'.")

    def add_edge(self, source_id: str, target_id: str, relationship: str, properties: Dict[str, Any]):
        """
        Adds a directed relationship (edge) between two nodes.
        
        Args:
            source_id (str): The ID of the source node.
            target_id (str): The ID of the target node.
            relationship (str): The type of relationship (e.g., 'CEO_of', 'competitor_of', 'affected_by').
            properties (Dict[str, Any]): A dictionary of attributes for the relationship (e.g., weight, date).
        """
        if self.graph.has_node(source_id) and self.graph.has_node(target_id):
            self.graph.add_edge(source_id, target_id, key=relationship, **properties)
            # print(f"Added relationship '{relationship}' from '{source_id}' to '{target_id}'.")

    def query_relationships(self, node_id: str, depth: int = 1) -> List[Tuple[str, str, str]]:
        """
        Finds all direct relationships for a given node up to a certain depth.
        
        Args:
            node_id (str): The ID of the node to query.
            depth (int): How many levels of relationships to explore.
            
        Returns:
            List[Tuple[str, str, str]]: A list of tuples representing (source, relationship, target).
        """
        if not self.graph.has_node(node_id):
            return []
            
        # Using ego_graph to find all neighbors within a certain radius (depth)
        subgraph = nx.ego_graph(self.graph, node_id, radius=depth)
        
        results = []
        for u, v, key, data in subgraph.edges(keys=True, data=True):
            results.append((u, key, v))
            
        return results

    def find_path(self, source_id: str, target_id: str) -> List[List[str]]:
        """
        Finds all simple paths between a source and a target node. This is useful for
        understanding indirect connections.
        
        Args:
            source_id (str): The starting node.
            target_id (str): The ending node.
            
        Returns:
            List[List[str]]: A list of paths, where each path is a list of node IDs.
        """
        if not self.graph.has_node(source_id) or not self.graph.has_node(target_id):
            return []
            
        return list(nx.all_simple_paths(self.graph, source=source_id, target=target_id))

# Example Usage:
if __name__ == '__main__':
    kg = KnowledgeGraph()

    # Add nodes
    kg.add_node('AAPL', 'Company', {'name': 'Apple Inc.', 'sector': 'Technology'})
    kg.add_node('TSMC', 'Company', {'name': 'Taiwan Semiconductor Manufacturing Company', 'sector': 'Semiconductors'})
    kg.add_node('inflation_cpi', 'EconomicIndicator', {'name': 'Consumer Price Index'})
    kg.add_node('interest_rates', 'EconomicIndicator', {'name': 'Federal Funds Rate'})

    # Add relationships
    kg.add_edge('TSMC', 'AAPL', 'supplier_of', {'product': 'A-series chips'})
    kg.add_edge('AAPL', 'TSMC', 'customer_of', {'product': 'A-series chips'})
    kg.add_edge('inflation_cpi', 'interest_rates', 'influences', {'effect': 'positive correlation'})
    kg.add_edge('interest_rates', 'AAPL', 'affects', {'effect': 'negative on valuation', 'mechanism': 'discount rate'})

    # Query the graph
    print(f"Relationships for AAPL (depth 1): {kg.query_relationships('AAPL', depth=1)}")
    print(f"Path between TSMC and AAPL: {kg.find_path('TSMC', 'AAPL')}")
