"""
Service for managing the knowledge graph of code relationships.
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

from loguru import logger
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, TransientError

from agent.core.models import Edge, EdgeType, Symbol, SymbolType


class GraphService:
    """
    Service for managing the knowledge graph of code relationships.
    """
    
    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize the graph service.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        
    def connect(self) -> None:
        """Connect to the Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info(f"Connected to Neo4j at {self.uri}")
            self._setup_constraints()
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
            
    def close(self) -> None:
        """Close the connection to the Neo4j database."""
        if self.driver:
            self.driver.close()
            logger.info("Closed connection to Neo4j")
            
    def _setup_constraints(self) -> None:
        """Set up database constraints for uniqueness."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            # Create uniqueness constraint for Symbol nodes
            session.run("""
                CREATE CONSTRAINT symbol_id_unique IF NOT EXISTS
                FOR (s:Symbol) REQUIRE s.id IS UNIQUE
            """)
            
            # Create uniqueness constraint for Edge nodes
            session.run("""
                CREATE CONSTRAINT edge_id_unique IF NOT EXISTS
                FOR (e:Edge) REQUIRE e.id IS UNIQUE
            """)
            
            # Create indexes for common queries
            session.run("""
                CREATE INDEX symbol_name_index IF NOT EXISTS
                FOR (s:Symbol) ON (s.name)
            """)
            
            session.run("""
                CREATE INDEX symbol_type_index IF NOT EXISTS
                FOR (s:Symbol) ON (s.type)
            """)
            
            session.run("""
                CREATE INDEX symbol_file_path_index IF NOT EXISTS
                FOR (s:Symbol) ON (s.file_path)
            """)
            
            session.run("""
                CREATE INDEX edge_type_index IF NOT EXISTS
                FOR (e:Edge) ON (e.type)
            """)
            
            logger.info("Set up database constraints and indexes")
            
    def upsert_symbol(self, symbol: Symbol) -> Symbol:
        """
        Insert or update a symbol in the graph.
        
        Args:
            symbol: Symbol to upsert
            
        Returns:
            The upserted symbol
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            result = session.run("""
                MERGE (s:Symbol {id: $id})
                SET s.name = $name,
                    s.type = $type,
                    s.file_path = $file_path,
                    s.language = $language,
                    s.start_line = $start_line,
                    s.end_line = $end_line,
                    s.start_column = $start_column,
                    s.end_column = $end_column,
                    s.docstring = $docstring,
                    s.signature = $signature,
                    s.parent_id = $parent_id,
                    s.metadata = $metadata,
                    s.repo_id = $repo_id
                RETURN s
            """, {
                "id": str(symbol.id),
                "name": symbol.name,
                "type": symbol.type.value,
                "file_path": symbol.file_path,
                "language": symbol.language.value,
                "start_line": symbol.start_line,
                "end_line": symbol.end_line,
                "start_column": symbol.start_column,
                "end_column": symbol.end_column,
                "docstring": symbol.docstring,
                "signature": symbol.signature,
                "parent_id": str(symbol.parent_id) if symbol.parent_id else None,
                "metadata": json.dumps(symbol.metadata),
                "repo_id": str(symbol.repo_id)
            })
            
            logger.debug(f"Upserted symbol: {symbol.name} ({symbol.type})")
            return symbol
            
    def upsert_edge(self, edge: Edge) -> Edge:
        """
        Insert or update an edge in the graph.
        
        Args:
            edge: Edge to upsert
            
        Returns:
            The upserted edge
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            result = session.run("""
                MERGE (e:Edge {id: $id})
                SET e.source_id = $source_id,
                    e.target_id = $target_id,
                    e.type = $type,
                    e.metadata = $metadata,
                    e.repo_id = $repo_id
                RETURN e
            """, {
                "id": str(edge.id),
                "source_id": str(edge.source_id),
                "target_id": str(edge.target_id),
                "type": edge.type.value,
                "metadata": json.dumps(edge.metadata),
                "repo_id": str(edge.repo_id)
            })
            
            # Create relationship between symbols
            session.run("""
                MATCH (source:Symbol {id: $source_id})
                MATCH (target:Symbol {id: $target_id})
                MERGE (source)-[r:RELATES {type: $type, edge_id: $edge_id}]->(target)
                SET r.metadata = $metadata
            """, {
                "source_id": str(edge.source_id),
                "target_id": str(edge.target_id),
                "type": edge.type.value,
                "edge_id": str(edge.id),
                "metadata": json.dumps(edge.metadata)
            })
            
            logger.debug(f"Upserted edge: {edge.type} from {edge.source_id} to {edge.target_id}")
            return edge
            
    def get_symbol(self, symbol_id: UUID) -> Optional[Symbol]:
        """
        Get a symbol by ID.
        
        Args:
            symbol_id: Symbol ID
            
        Returns:
            Symbol or None if not found
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Symbol {id: $id})
                RETURN s
            """, {"id": str(symbol_id)})
            
            record = result.single()
            if not record:
                return None
                
            node = record["s"]
            return self._node_to_symbol(node)
            
    def get_edge(self, edge_id: UUID) -> Optional[Edge]:
        """
        Get an edge by ID.
        
        Args:
            edge_id: Edge ID
            
        Returns:
            Edge or None if not found
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Edge {id: $id})
                RETURN e
            """, {"id": str(edge_id)})
            
            record = result.single()
            if not record:
                return None
                
            node = record["e"]
            return self._node_to_edge(node)
            
    def get_symbols_by_repo(self, repo_id: UUID) -> List[Symbol]:
        """
        Get all symbols in a repository.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            List of symbols
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Symbol {repo_id: $repo_id})
                RETURN s
                ORDER BY s.file_path, s.start_line
            """, {"repo_id": str(repo_id)})
            
            symbols = []
            for record in result:
                node = record["s"]
                symbols.append(self._node_to_symbol(node))
                
            return symbols
            
    def get_edges_by_repo(self, repo_id: UUID) -> List[Edge]:
        """
        Get all edges in a repository.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            List of edges
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Edge {repo_id: $repo_id})
                RETURN e
            """, {"repo_id": str(repo_id)})
            
            edges = []
            for record in result:
                node = record["e"]
                edges.append(self._node_to_edge(node))
                
            return edges
            
    def get_symbols_by_file(self, repo_id: UUID, file_path: str) -> List[Symbol]:
        """
        Get all symbols in a file.
        
        Args:
            repo_id: Repository ID
            file_path: Path to the file
            
        Returns:
            List of symbols
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Symbol {repo_id: $repo_id, file_path: $file_path})
                RETURN s
                ORDER BY s.start_line
            """, {"repo_id": str(repo_id), "file_path": file_path})
            
            symbols = []
            for record in result:
                node = record["s"]
                symbols.append(self._node_to_symbol(node))
                
            return symbols
            
    def get_call_graph(self, repo_id: UUID) -> Dict[str, List[str]]:
        """
        Get the call graph for a repository.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            Dictionary mapping function names to lists of called function names
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            result = session.run("""
                MATCH (caller:Symbol {repo_id: $repo_id})-[:RELATES {type: 'calls'}]->(callee:Symbol {repo_id: $repo_id})
                RETURN caller.name AS caller, callee.name AS callee
            """, {"repo_id": str(repo_id)})
            
            call_graph = {}
            for record in result:
                caller = record["caller"]
                callee = record["callee"]
                
                if caller not in call_graph:
                    call_graph[caller] = []
                call_graph[caller].append(callee)
                
            return call_graph
            
    def get_endpoints_without_validation(self, repo_id: UUID) -> List[Dict[str, Any]]:
        """
        Get endpoints that don't have validation.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            List of endpoint information
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            # This is a simplified query that looks for functions that take parameters
            # but don't appear to have validation logic
            result = session.run("""
                MATCH (func:Symbol {repo_id: $repo_id, type: 'function'})
                WHERE func.metadata IS NOT NULL
                AND func.metadata.parameters IS NOT NULL
                AND size(func.metadata.parameters) > 0
                AND NOT EXISTS {
                    MATCH (func)-[:RELATES {type: 'calls'}]->(validator:Symbol)
                    WHERE validator.name CONTAINS 'validate' OR validator.name CONTAINS 'check'
                }
                RETURN func.name AS name, func.file_path AS file_path, func.metadata.parameters AS parameters
            """, {"repo_id": str(repo_id)})
            
            endpoints = []
            for record in result:
                endpoints.append({
                    "name": record["name"],
                    "file_path": record["file_path"],
                    "parameters": record["parameters"]
                })
                
            return endpoints
            
    def get_orphan_symbols(self, repo_id: UUID) -> List[Symbol]:
        """
        Get symbols that are not referenced by any other symbol.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            List of orphan symbols
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:Symbol {repo_id: $repo_id})
                WHERE NOT EXISTS {
                    MATCH ()-[:RELATES]->(s)
                }
                AND s.type <> 'module'
                RETURN s
            """, {"repo_id": str(repo_id)})
            
            orphans = []
            for record in result:
                node = record["s"]
                orphans.append(self._node_to_symbol(node))
                
            return orphans
            
    def get_cycles(self, repo_id: UUID) -> List[List[str]]:
        """
        Get cycles in the dependency graph.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            List of cycles, where each cycle is a list of symbol names
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        with self.driver.session() as session:
            # Use a Cypher query to detect cycles
            result = session.run("""
                MATCH (s1:Symbol {repo_id: $repo_id})-[:RELATES*]->(s2:Symbol {repo_id: $repo_id})
                WHERE s1 = s2
                WITH s1, s2
                MATCH path = (s1)-[:RELATES*]->(s2)
                RETURN [node IN nodes(path) | node.name] AS cycle
                LIMIT 100
            """, {"repo_id": str(repo_id)})
            
            cycles = []
            for record in result:
                cycle = record["cycle"]
                # Ensure we have a valid cycle (at least 2 nodes)
                if len(cycle) >= 2:
                    cycles.append(cycle)
                    
            return cycles
            
    def export_graphml(self, repo_id: UUID, output_path: str) -> None:
        """
        Export the knowledge graph to GraphML format.
        
        Args:
            repo_id: Repository ID
            output_path: Path to save the GraphML file
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        # This is a simplified implementation
        # In a real implementation, we would use a library like networkx to generate proper GraphML
        
        with self.driver.session() as session:
            # Get all symbols
            symbols_result = session.run("""
                MATCH (s:Symbol {repo_id: $repo_id})
                RETURN s
            """, {"repo_id": str(repo_id)})
            
            # Get all edges
            edges_result = session.run("""
                MATCH (s1:Symbol {repo_id: $repo_id})-[r:RELATES]->(s2:Symbol {repo_id: $repo_id})
                RETURN s1.id AS source_id, s2.id AS target_id, r.type AS type
            """, {"repo_id": str(repo_id)})
            
            # Generate GraphML
            with open(output_path, "w") as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns"\n')
                f.write('    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
                f.write('    xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns\n')
                f.write('    http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n')
                
                # Define key attributes
                f.write('  <key id="name" for="node" attr.name="name" attr.type="string"/>\n')
                f.write('  <key id="type" for="node" attr.name="type" attr.type="string"/>\n')
                f.write('  <key id="file_path" for="node" attr.name="file_path" attr.type="string"/>\n')
                f.write('  <key id="relationship_type" for="edge" attr.name="type" attr.type="string"/>\n')
                
                f.write('  <graph id="G" edgedefault="directed">\n')
                
                # Add nodes
                for record in symbols_result:
                    node = record["s"]
                    f.write(f'    <node id="{node["id"]}">\n')
                    f.write(f'      <data key="name">{node["name"]}</data>\n')
                    f.write(f'      <data key="type">{node["type"]}</data>\n')
                    f.write(f'      <data key="file_path">{node["file_path"]}</data>\n')
                    f.write('    </node>\n')
                
                # Add edges
                for record in edges_result:
                    f.write(f'    <edge source="{record["source_id"]}" target="{record["target_id"]}">\n')
                    f.write(f'      <data key="relationship_type">{record["type"]}</data>\n')
                    f.write('    </edge>\n')
                
                f.write('  </graph>\n')
                f.write('</graphml>\n')
                
            logger.info(f"Exported graph to {output_path}")
            
    def import_ir(self, ir_data: Dict[str, Any]) -> None:
        """
        Import intermediate representation data into the graph.
        
        Args:
            ir_data: Intermediate representation data
        """
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j")
            
        # Import symbols
        for symbol_data in ir_data.get("symbols", []):
            symbol = Symbol(**symbol_data)
            self.upsert_symbol(symbol)
            
        # Import edges
        for edge_data in ir_data.get("edges", []):
            edge = Edge(**edge_data)
            self.upsert_edge(edge)
            
        logger.info(f"Imported {len(ir_data.get('symbols', []))} symbols and {len(ir_data.get('edges', []))} edges")
            
    def _node_to_symbol(self, node) -> Symbol:
        """
        Convert a Neo4j node to a Symbol object.
        
        Args:
            node: Neo4j node
            
        Returns:
            Symbol object
        """
        metadata = {}
        if node.get("metadata"):
            try:
                metadata = json.loads(node["metadata"])
            except json.JSONDecodeError:
                metadata = {}
                
        return Symbol(
            id=UUID(node["id"]),
            name=node["name"],
            type=SymbolType(node["type"]),
            file_path=node["file_path"],
            language=Language(node["language"]),
            start_line=node["start_line"],
            end_line=node["end_line"],
            start_column=node["start_column"],
            end_column=node["end_column"],
            docstring=node.get("docstring"),
            signature=node.get("signature"),
            parent_id=UUID(node["parent_id"]) if node.get("parent_id") else None,
            metadata=metadata,
            repo_id=UUID(node["repo_id"])
        )
        
    def _node_to_edge(self, node) -> Edge:
        """
        Convert a Neo4j node to an Edge object.
        
        Args:
            node: Neo4j node
            
        Returns:
            Edge object
        """
        metadata = {}
        if node.get("metadata"):
            try:
                metadata = json.loads(node["metadata"])
            except json.JSONDecodeError:
                metadata = {}
                
        return Edge(
            id=UUID(node["id"]),
            source_id=UUID(node["source_id"]),
            target_id=UUID(node["target_id"]),
            type=EdgeType(node["type"]),
            metadata=metadata,
            repo_id=UUID(node["repo_id"])
        )
