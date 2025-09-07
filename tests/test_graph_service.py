"""
Tests for knowledge graph service functionality.
"""

import unittest
from unittest.mock import patch, MagicMock

from agent.graph.service import GraphService
from agent.core.models import Symbol, Edge, SymbolType, EdgeType, Language


class TestGraphService(unittest.TestCase):
    """Test cases for graph service."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph_service = GraphService(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password"
        )

    @patch('agent.graph.service.GraphDatabase.driver')
    def test_connect(self, mock_driver_class):
        """Test connecting to Neo4j."""
        # Setup mock
        mock_driver = MagicMock()
        mock_driver_class.return_value = mock_driver
        
        # Call function
        self.graph_service.connect()
        
        # Assertions
        mock_driver_class.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "password")
        )
        mock_driver.session.assert_called()
        self.assertEqual(self.graph_service.driver, mock_driver)

    @patch('agent.graph.service.GraphService._setup_constraints')
    def test_close(self, mock_setup_constraints):
        """Test closing the connection to Neo4j."""
        # Setup mock driver
        self.graph_service.driver = MagicMock()
        
        # Call function
        self.graph_service.close()
        
        # Assertions
        self.graph_service.driver.close.assert_called_once()

    def test_setup_constraints(self):
        """Test setting up database constraints."""
        # Setup mock driver and session
        mock_session = MagicMock()
        self.graph_service.driver = MagicMock()
        self.graph_service.driver.session.return_value.__enter__.return_value = mock_session
        
        # Call function
        self.graph_service._setup_constraints()
        
        # Assertions
        self.assertTrue(mock_session.run.call_count >= 7)  # At least 7 constraints/indexes

    def test_upsert_symbol(self):
        """Test upserting a symbol."""
        # Setup mock driver and session
        mock_session = MagicMock()
        self.graph_service.driver = MagicMock()
        self.graph_service.driver.session.return_value.__enter__.return_value = mock_session
        
        # Create test symbol
        symbol = Symbol(
            id="test-symbol-id",
            name="test_function",
            type=SymbolType.FUNCTION,
            file_path="src/main.py",
            language=Language.PYTHON,
            start_line=1,
            end_line=5,
            start_column=0,
            end_column=0,
            repo_id="test-repo-id"
        )
        
        # Call function
        result = self.graph_service.upsert_symbol(symbol)
        
        # Assertions
        mock_session.run.assert_called_once()
        self.assertEqual(result, symbol)

    def test_upsert_edge(self):
        """Test upserting an edge."""
        # Setup mock driver and session
        mock_session = MagicMock()
        self.graph_service.driver = MagicMock()
        self.graph_service.driver.session.return_value.__enter__.return_value = mock_session
        
        # Create test edge
        edge = Edge(
            id="test-edge-id",
            source_id="source-id",
            target_id="target-id",
            type=EdgeType.CALLS,
            repo_id="test-repo-id"
        )
        
        # Call function
        result = self.graph_service.upsert_edge(edge)
        
        # Assertions
        self.assertEqual(mock_session.run.call_count, 2)  # One for edge, one for relationship
        self.assertEqual(result, edge)

    def test_get_symbol(self):
        """Test getting a symbol by ID."""
        # Setup mock driver and session
        mock_session = MagicMock()
        self.graph_service.driver = MagicMock()
        self.graph_service.driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock result
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "id": "test-symbol-id",
            "name": "test_function",
            "type": "function",
            "file_path": "src/main.py",
            "language": "python",
            "start_line": 1,
            "end_line": 5,
            "start_column": 0,
            "end_column": 0,
            "docstring": None,
            "signature": None,
            "parent_id": None,
            "metadata": "{}",
            "repo_id": "test-repo-id"
        }[key]
        mock_session.run.return_value.single.return_value = mock_record
        
        # Call function
        from uuid import uuid
        symbol = self.graph_service.get_symbol(uuid.UUID("test-symbol-id"))
        
        # Assertions
        mock_session.run.assert_called_once()
        self.assertIsNotNone(symbol)
        self.assertEqual(symbol.name, "test_function")

    def test_get_edge(self):
        """Test getting an edge by ID."""
        # Setup mock driver and session
        mock_session = MagicMock()
        self.graph_service.driver = MagicMock()
        self.graph_service.driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock result
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "id": "test-edge-id",
            "source_id": "source-id",
            "target_id": "target-id",
            "type": "calls",
            "metadata": "{}",
            "repo_id": "test-repo-id"
        }[key]
        mock_session.run.return_value.single.return_value = mock_record
        
        # Call function
        from uuid import uuid
        edge = self.graph_service.get_edge(uuid.UUID("test-edge-id"))
        
        # Assertions
        mock_session.run.assert_called_once()
        self.assertIsNotNone(edge)
        self.assertEqual(edge.type, EdgeType.CALLS)

    def test_get_symbols_by_repo(self):
        """Test getting symbols by repository ID."""
        # Setup mock driver and session
        mock_session = MagicMock()
        self.graph_service.driver = MagicMock()
        self.graph_service.driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock result
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "id": "test-symbol-id",
            "name": "test_function",
            "type": "function",
            "file_path": "src/main.py",
            "language": "python",
            "start_line": 1,
            "end_line": 5,
            "start_column": 0,
            "end_column": 0,
            "docstring": None,
            "signature": None,
            "parent_id": None,
            "metadata": "{}",
            "repo_id": "test-repo-id"
        }[key]
        mock_session.run.return_value = [mock_record]
        
        # Call function
        from uuid import uuid
        symbols = self.graph_service.get_symbols_by_repo(uuid.UUID("test-repo-id"))
        
        # Assertions
        mock_session.run.assert_called_once()
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0].name, "test_function")

    def test_get_call_graph(self):
        """Test getting the call graph."""
        # Setup mock driver and session
        mock_session = MagicMock()
        self.graph_service.driver = MagicMock()
        self.graph_service.driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock result
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "caller": "function1",
            "callee": "function2"
        }[key]
        mock_session.run.return_value = [mock_record]
        
        # Call function
        from uuid import uuid
        call_graph = self.graph_service.get_call_graph(uuid.UUID("test-repo-id"))
        
        # Assertions
        mock_session.run.assert_called_once()
        self.assertEqual(call_graph, {"function1": ["function2"]})

    def test_export_graphml(self):
        """Test exporting the graph to GraphML."""
        # Setup mock driver and session
        mock_session = MagicMock()
        self.graph_service.driver = MagicMock()
        self.graph_service.driver.session.return_value.__enter__.return_value = mock_session
        
        # Mock results
        mock_symbol_record = MagicMock()
        mock_symbol_record.__getitem__.side_effect = lambda key: {
            "id": "symbol-id",
            "name": "test_function",
            "type": "function",
            "file_path": "src/main.py"
        }[key]
        
        mock_edge_record = MagicMock()
        mock_edge_record.__getitem__.side_effect = lambda key: {
            "source_id": "source-id",
            "target_id": "target-id",
            "type": "calls"
        }[key]
        
        mock_session.run.side_effect = [
            [mock_symbol_record],  # Symbols
            [mock_edge_record]    # Edges
        ]
        
        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Call function
            from uuid import uuid
            self.graph_service.export_graphml(uuid.UUID("test-repo-id"), temp_path)
            
            # Assertions
            self.assertEqual(mock_session.run.call_count, 2)
            
            # Check that file was created
            with open(temp_path, "r") as f:
                content = f.read()
                self.assertIn("graphml", content)
                self.assertIn("symbol-id", content)
                self.assertIn("source-id", content)
                self.assertIn("target-id", content)
        finally:
            # Clean up
            import os
            os.unlink(temp_path)

    def test_import_ir(self):
        """Test importing intermediate representation data."""
        # Setup mock driver and session
        mock_session = MagicMock()
        self.graph_service.driver = MagicMock()
        self.graph_service.driver.session.return_value.__enter__.return_value = mock_session
        
        # Create test IR data
        ir_data = {
            "symbols": [
                {
                    "id": "symbol-id",
                    "name": "test_function",
                    "type": "function",
                    "file_path": "src/main.py",
                    "language": "python",
                    "start_line": 1,
                    "end_line": 5,
                    "start_column": 0,
                    "end_column": 0,
                    "repo_id": "test-repo-id"
                }
            ],
            "edges": [
                {
                    "id": "edge-id",
                    "source_id": "source-id",
                    "target_id": "target-id",
                    "type": "calls",
                    "repo_id": "test-repo-id"
                }
            ]
        }
        
        # Call function
        self.graph_service.import_ir(ir_data)
        
        # Assertions
        self.assertEqual(mock_session.run.call_count, 2)  # One for symbol, one for edge


if __name__ == "__main__":
    unittest.main()
