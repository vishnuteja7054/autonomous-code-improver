"""
Tests for code parsing functionality.
"""

import unittest
from unittest.mock import patch, MagicMock

from agent.ingestion.parser import (
    parse_file,
    get_tree_sitter_language,
    extract_python_symbols_and_edges,
    extract_python_function,
    extract_python_class,
    extract_python_imports,
    extract_python_calls
)
from agent.core.models import Language, ParseUnit, SymbolType, EdgeType


class TestParseFile(unittest.TestCase):
    """Test cases for file parsing."""

    def setUp(self):
        """Set up test fixtures."""
        self.parse_unit = ParseUnit(
            id="test-parse-unit",
            repo_id="test-repo-id",
            path="src/main.py",
            language=Language.PYTHON,
            content="print('Hello, world!')"
        )

    @patch('agent.ingestion.parser.Parser')
    def test_parse_file_python(self, mock_parser_class):
        """Test parsing a Python file."""
        # Setup mocks
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        
        mock_tree = MagicMock()
        mock_parser.parse.return_value = mock_tree
        
        mock_root_node = MagicMock()
        mock_tree.root_node = mock_root_node
        
        # Mock symbol and edge extraction
        with patch('agent.ingestion.parser.extract_python_symbols_and_edges') as mock_extract:
            mock_extract.return_value = ([], [])
            
            # Call function
            result = parse_file(self.parse_unit)
            
            # Assertions
            mock_parser.set_language.assert_called_once()
            mock_parser.parse.assert_called_once_with(b"print('Hello, world!')")
            mock_extract.assert_called_once_with(mock_root_node, "src/main.py", Language.PYTHON, "test-repo-id")
            self.assertEqual(result, self.parse_unit)

    def test_get_tree_sitter_language(self):
        """Test getting Tree-sitter language."""
        # Test Python
        lang = get_tree_sitter_language(Language.PYTHON)
        self.assertIsNotNone(lang)
        
        # Test TypeScript
        lang = get_tree_sitter_language(Language.TYPESCRIPT)
        self.assertIsNotNone(lang)
        
        # Test unsupported language
        lang = get_tree_sitter_language(Language.JAVA)
        self.assertIsNone(lang)

    @patch('agent.ingestion.parser.extract_python_function')
    @patch('agent.ingestion.parser.extract_python_class')
    @patch('agent.ingestion.parser.extract_python_imports')
    @patch('agent.ingestion.parser.extract_python_calls')
    def test_extract_python_symbols_and_edges(
        self,
        mock_extract_calls,
        mock_extract_imports,
        mock_extract_class,
        mock_extract_function
    ):
        """Test extracting symbols and edges from Python code."""
        # Setup mocks
        mock_root_node = MagicMock()
        mock_root_node.children_by_type.side_effect = lambda node_type: []
        
        # Call function
        symbols, edges = extract_python_symbols_and_edges(
            mock_root_node,
            "src/main.py",
            Language.PYTHON,
            "test-repo-id"
        )
        
        # Assertions
        self.assertEqual(symbols, [])
        self.assertEqual(edges, [])
        mock_root_node.children_by_type.assert_any_call("function_definition")
        mock_root_node.children_by_type.assert_any_call("class_definition")
        mock_root_node.children_by_type.assert_any_call("import_statement")
        mock_root_node.children_by_type.assert_any_call("call")

    def test_extract_python_function(self):
        """Test extracting a Python function."""
        # Create a mock function node
        mock_node = MagicMock()
        mock_node.start_point = (0, 0)
        mock_node.end_point = (4, 0)
        
        # Mock name node
        mock_name_node = MagicMock()
        mock_name_node.text.decode.return_value = "test_function"
        mock_node.child_by_field_name.return_value = mock_name_node
        
        # Mock parameters node
        mock_params_node = MagicMock()
        mock_params_node.children = [
            MagicMock(type="identifier", text=MagicMock(decode=MagicMock(return_value="arg1"))),
            MagicMock(type="identifier", text=MagicMock(decode=MagicMock(return_value="arg2")))
        ]
        mock_node.child_by_field_name.side_effect = lambda field: {
            "name": mock_name_node,
            "parameters": mock_params_node,
            "body": MagicMock(children=[])
        }.get(field)
        
        # Call function
        symbol = extract_python_function(mock_node, "src/main.py", "test-repo-id")
        
        # Assertions
        self.assertIsNotNone(symbol)
        self.assertEqual(symbol.name, "test_function")
        self.assertEqual(symbol.type, SymbolType.FUNCTION)
        self.assertEqual(symbol.file_path, "src/main.py")
        self.assertEqual(symbol.language, Language.PYTHON)
        self.assertEqual(symbol.start_line, 1)
        self.assertEqual(symbol.end_line, 5)
        self.assertEqual(symbol.signature, "test_function(arg1, arg2)")

    def test_extract_python_class(self):
        """Test extracting a Python class."""
        # Create a mock class node
        mock_node = MagicMock()
        mock_node.start_point = (0, 0)
        mock_node.end_point = (6, 0)
        
        # Mock name node
        mock_name_node = MagicMock()
        mock_name_node.text.decode.return_value = "TestClass"
        mock_node.child_by_field_name.return_value = mock_name_node
        
        # Mock arguments node
        mock_args_node = MagicMock()
        mock_args_node.children = [
            MagicMock(type="identifier", text=MagicMock(decode=MagicMock(return_value="BaseClass")))
        ]
        mock_node.child_by_field_name.side_effect = lambda field: {
            "name": mock_name_node,
            "arguments": mock_args_node,
            "body": MagicMock(children=[])
        }.get(field)
        
        # Call function
        symbol = extract_python_class(mock_node, "src/main.py", "test-repo-id")
        
        # Assertions
        self.assertIsNotNone(symbol)
        self.assertEqual(symbol.name, "TestClass")
        self.assertEqual(symbol.type, SymbolType.CLASS)
        self.assertEqual(symbol.file_path, "src/main.py")
        self.assertEqual(symbol.language, Language.PYTHON)
        self.assertEqual(symbol.start_line, 1)
        self.assertEqual(symbol.end_line, 7)
        self.assertEqual(symbol.metadata["superclasses"], ["BaseClass"])

    def test_extract_python_imports(self):
        """Test extracting Python imports."""
        # Create a mock import node
        mock_node = MagicMock()
        mock_node.children = [MagicMock(type="import")]
        
        # Create mock symbols
        symbols = [
            MagicMock(
                name="function1",
                type=SymbolType.FUNCTION,
                id="func1-id"
            ),
            MagicMock(
                name="function2",
                type=SymbolType.FUNCTION,
                id="func2-id"
            )
        ]
        
        # Call function
        edges = extract_python_imports(mock_node, symbols, "test-repo-id")
        
        # Assertions
        self.assertEqual(len(edges), 2)
        self.assertEqual(edges[0].type, EdgeType.IMPORTS)
        self.assertEqual(edges[0].source_id, "func1-id")
        self.assertEqual(edges[1].type, EdgeType.IMPORTS)
        self.assertEqual(edges[1].source_id, "func2-id")

    def test_extract_python_calls(self):
        """Test extracting Python function calls."""
        # Create a mock call node
        mock_node = MagicMock()
        
        # Mock function node
        mock_function_node = MagicMock()
        mock_function_node.type = "identifier"
        mock_function_node.text.decode.return_value = "called_function"
        mock_node.child_by_field_name.return_value = mock_function_node
        
        # Create mock symbols
        symbols = [
            MagicMock(
                name="caller_function",
                type=SymbolType.FUNCTION,
                id="caller-id"
            ),
            MagicMock(
                name="called_function",
                type=SymbolType.FUNCTION,
                id="called-id"
            )
        ]
        
        # Call function
        edges = extract_python_calls(mock_node, symbols, "test-repo-id")
        
        # Assertions
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0].type, EdgeType.CALLS)
        self.assertEqual(edges[0].source_id, "caller-id")
        self.assertEqual(edges[0].target_id, "called-id")


if __name__ == "__main__":
    unittest.main()
