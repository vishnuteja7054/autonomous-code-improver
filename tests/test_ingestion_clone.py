"""
Tests for repository cloning functionality.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from agent.ingestion.clone import clone_repository, cleanup_clone, get_repo_info
from agent.core.models import RepoSpec


class TestCloneRepository(unittest.TestCase):
    """Test cases for repository cloning."""

    def setUp(self):
        """Set up test fixtures."""
        self.repo_spec = RepoSpec(
            id="test-repo-id",
            url="https://github.com/example/repo.git"
        )

    @patch('agent.ingestion.clone.Repo')
    def test_clone_repository_with_branch(self, mock_repo_class):
        """Test cloning a repository with a specific branch."""
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.clone_from.return_value = mock_repo
        
        # Call function
        clone_path, repo = clone_repository(
            self.repo_spec,
            target_dir="/tmp/test",
            branch="develop"
        )
        
        # Assertions
        mock_repo_class.clone_from.assert_called_once_with(
            url="https://github.com/example/repo.git",
            to_path="/tmp/test/repo",
            branch="develop"
        )
        self.assertEqual(clone_path, "/tmp/test/repo")
        self.assertEqual(repo, mock_repo)

    @patch('agent.ingestion.clone.Repo')
    def test_clone_repository_with_commit(self, mock_repo_class):
        """Test cloning a repository with a specific commit."""
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.clone_from.return_value = mock_repo
        
        # Call function
        clone_path, repo = clone_repository(
            self.repo_spec,
            target_dir="/tmp/test",
            commit="abc123"
        )
        
        # Assertions
        mock_repo_class.clone_from.assert_called_once_with(
            url="https://github.com/example/repo.git",
            to_path="/tmp/test/repo"
        )
        mock_repo.git.checkout.assert_called_once_with("abc123")
        self.assertEqual(clone_path, "/tmp/test/repo")
        self.assertEqual(repo, mock_repo)

    @patch('agent.ingestion.clone.Repo')
    def test_clone_repository_creates_temp_dir(self, mock_repo_class):
        """Test that clone_repository creates a temporary directory when no target_dir is provided."""
        # Setup mock
        mock_repo = MagicMock()
        mock_repo_class.clone_from.return_value = mock_repo
        
        with patch('agent.ingestion.clone.tempfile.mkdtemp') as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/test-123"
            
            # Call function
            clone_path, repo = clone_repository(self.repo_spec)
            
            # Assertions
            mock_mkdtemp.assert_called_once()
            self.assertTrue(clone_path.startswith("/tmp/test-123/"))

    @patch('agent.ingestion.clone.Repo')
    @patch('agent.ingestion.clone.shutil.rmtree')
    def test_clone_repository_cleanup_on_failure(self, mock_rmtree, mock_repo_class):
        """Test that clone_repository cleans up on failure."""
        # Setup mock to raise exception
        mock_repo_class.clone_from.side_effect = Exception("Clone failed")
        
        with patch('agent.ingestion.clone.tempfile.mkdtemp') as mock_mkdtemp:
            mock_mkdtemp.return_value = "/tmp/test-123"
            
            # Call function and expect exception
            with self.assertRaises(Exception):
                clone_repository(self.repo_spec)
            
            # Assertions
            mock_rmtree.assert_called_once_with("/tmp/test-123/repo")

    def test_cleanup_clone(self):
        """Test cleaning up a cloned repository."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_dir = os.path.join(temp_dir, "repo")
            os.makedirs(repo_dir)
            
            # Verify directory exists
            self.assertTrue(os.path.exists(repo_dir))
            
            # Clean up
            cleanup_clone(repo_dir)
            
            # Verify directory is removed
            self.assertFalse(os.path.exists(repo_dir))

    @patch('agent.ingestion.clone.Repo')
    def test_get_repo_info(self, mock_repo_class):
        """Test getting repository information."""
        # Setup mock
        mock_repo = MagicMock()
        mock_repo.head.commit.hexsha = "abc123"
        mock_repo.head.commit.message = "Initial commit"
        mock_repo.head.commit.committed_datetime.isoformat.return_value = "2023-01-01T00:00:00"
        mock_repo.head.commit.author.name = "John Doe"
        mock_repo.active_branch.name = "main"
        mock_repo.remotes = [MagicMock(url="https://github.com/example/repo.git")]
        mock_repo.is_dirty.return_value = False
        mock_repo.untracked_files = []
        
        mock_repo_class.return_value = mock_repo
        
        # Call function
        info = get_repo_info("/tmp/repo")
        
        # Assertions
        self.assertEqual(info["commit"], "abc123")
        self.assertEqual(info["commit_message"], "Initial commit")
        self.assertEqual(info["branch"], "main")
        self.assertEqual(info["remote_url"], "https://github.com/example/repo.git")
        self.assertFalse(info["is_dirty"])

    @patch('agent.ingestion.clone.Repo')
    def test_get_repo_info_with_error(self, mock_repo_class):
        """Test getting repository information when an error occurs."""
        # Setup mock to raise exception
        mock_repo_class.side_effect = Exception("Not a git repository")
        
        # Call function
        info = get_repo_info("/tmp/repo")
        
        # Assertions
        self.assertIn("error", info)
        self.assertEqual(info["error"], "Not a git repository")


if __name__ == "__main__":
    unittest.main()
