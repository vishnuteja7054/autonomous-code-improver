"""
Tests for repository indexing functionality.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from agent.ingestion.indexer import (
    index_repository,
    should_exclude_file,
    detect_language,
    is_binary_file,
    get_file_stats
)
from agent.core.models import Language, RepoSpec


class TestIndexRepository(unittest.TestCase):
    """Test cases for repository indexing."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_spec = RepoSpec(
            id="test-repo-id",
            url="https://github.com/example/repo.git",
            languages=[Language.PYTHON]
        )

    def test_index_repository_with_python_files(self):
        """Test indexing a repository with Python files."""
        # Create a temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Python files
            os.makedirs(os.path.join(temp_dir, "src"))
            with open(os.path.join(temp_dir, "src", "main.py"), "w") as f:
                f.write("print('Hello, world!')")
            
            with open(os.path.join(temp_dir, "src", "utils.py"), "w") as f:
                f.write("def helper():\n    return 'help'")
            
            # Create a non-Python file
            with open(os.path.join(temp_dir, "README.md"), "w") as f:
                f.write("# Test Repository")
            
            # Call function
            parse_units = index_repository(temp_dir, self.repo_spec)
            
            # Assertions
            self.assertEqual(len(parse_units), 2)
            self.assertEqual(parse_units[0].path, "src/main.py")
            self.assertEqual(parse_units[0].language, Language.PYTHON)
            self.assertEqual(parse_units[1].path, "src/utils.py")
            self.assertEqual(parse_units[1].language, Language.PYTHON)

    def test_index_repository_with_exclude_patterns(self):
        """Test indexing a repository with exclude patterns."""
        # Create a temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Python files
            os.makedirs(os.path.join(temp_dir, "src"))
            with open(os.path.join(temp_dir, "src", "main.py"), "w") as f:
                f.write("print('Hello, world!')")
            
            # Create test files
            os.makedirs(os.path.join(temp_dir, "tests"))
            with open(os.path.join(temp_dir, "tests", "test_main.py"), "w") as f:
                f.write("def test_main():\n    assert True")
            
            # Set exclude patterns
            self.repo_spec.exclude_patterns = ["tests/*"]
            
            # Call function
            parse_units = index_repository(temp_dir, self.repo_spec)
            
            # Assertions
            self.assertEqual(len(parse_units), 1)
            self.assertEqual(parse_units[0].path, "src/main.py")

    def test_index_repository_with_language_filter(self):
        """Test indexing a repository with language filter."""
        # Create a temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Python and JavaScript files
            with open(os.path.join(temp_dir, "main.py"), "w") as f:
                f.write("print('Hello, world!')")
            
            with open(os.path.join(temp_dir, "app.js"), "w") as f:
                f.write("console.log('Hello, world!');")
            
            # Set language filter to Python only
            self.repo_spec.languages = [Language.PYTHON]
            
            # Call function
            parse_units = index_repository(temp_dir, self.repo_spec)
            
            # Assertions
            self.assertEqual(len(parse_units), 1)
            self.assertEqual(parse_units[0].path, "main.py")
            self.assertEqual(parse_units[0].language, Language.PYTHON)

    def test_should_exclude_file(self):
        """Test file exclusion logic."""
        # Test suffix pattern
        self.assertTrue(should_exclude_file("test.py", ["*.pyc"]))
        self.assertFalse(should_exclude_file("test.py", ["*.js"]))
        
        # Test prefix pattern
        self.assertTrue(should_exclude_file("tests/test.py", ["tests/*"]))
        self.assertFalse(should_exclude_file("src/test.py", ["tests/*"]))
        
        # Test exact match
        self.assertTrue(should_exclude_file("__pycache__", ["__pycache__"]))
        self.assertFalse(should_exclude_file("src", ["__pycache__"]))

    def test_detect_language(self):
        """Test language detection."""
        self.assertEqual(detect_language("main.py"), Language.PYTHON)
        self.assertEqual(detect_language("app.js"), Language.JAVASCRIPT)
        self.assertEqual(detect_language("component.tsx"), Language.TYPESCRIPT)
        self.assertEqual(detect_language("style.css"), None)

    def test_is_binary_file(self):
        """Test binary file detection."""
        # Create a temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a text file
            with open(os.path.join(temp_dir, "text.txt"), "w") as f:
                f.write("This is a text file")
            
            # Create a binary file
            with open(os.path.join(temp_dir, "binary.bin"), "wb") as f:
                f.write(b"\x00\x01\x02\x03")
            
            # Test text file
            self.assertFalse(is_binary_file(os.path.join(temp_dir, "text.txt")))
            
            # Test binary file
            self.assertTrue(is_binary_file(os.path.join(temp_dir, "binary.bin")))

    def test_get_file_stats(self):
        """Test getting file statistics."""
        # Create a temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Python files
            os.makedirs(os.path.join(temp_dir, "src"))
            with open(os.path.join(temp_dir, "src", "main.py"), "w") as f:
                f.write("print('Hello, world!')")
            
            with open(os.path.join(temp_dir, "src", "utils.py"), "w") as f:
                f.write("def helper():\n    return 'help'")
            
            # Create a JavaScript file
            with open(os.path.join(temp_dir, "app.js"), "w") as f:
                f.write("console.log('Hello, world!');")
            
            # Call function
            stats = get_file_stats(temp_dir)
            
            # Assertions
            self.assertEqual(stats["total_files"], 3)
            self.assertEqual(stats["files_by_language"]["python"]["count"], 2)
            self.assertEqual(stats["files_by_language"]["javascript"]["count"], 1)
            self.assertGreater(stats["total_size_bytes"], 0)
            self.assertIsNotNone(stats["largest_file"])
            self.assertIsNotNone(stats["smallest_file"])


if __name__ == "__main__":
    unittest.main()
