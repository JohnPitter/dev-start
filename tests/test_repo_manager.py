"""Tests for repository manager."""
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from src.repo_manager import RepositoryManager
from src.proxy_manager import ProxyManager


class TestRepositoryManager(unittest.TestCase):
    """Test cases for RepositoryManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.proxy_manager = ProxyManager()
        self.repo_manager = RepositoryManager(self.proxy_manager)

    def test_get_repo_name_from_url(self):
        """Test extracting repository name from URL."""
        test_cases = [
            ('https://github.com/user/myrepo.git', 'myrepo'),
            ('https://github.com/user/myrepo', 'myrepo'),
            ('https://gitlab.com/org/project.git', 'project'),
            ('git@github.com:user/repo.git', 'repo'),  # SSH URL - splits on : and removes .git
        ]

        for url, expected_name in test_cases:
            result = self.repo_manager.get_repo_name(url)
            self.assertEqual(result, expected_name)

    def test_get_repo_name_removes_git_suffix(self):
        """Test that .git suffix is removed."""
        url = 'https://github.com/user/test-repo.git'
        result = self.repo_manager.get_repo_name(url)
        self.assertEqual(result, 'test-repo')
        self.assertNotIn('.git', result)

    def test_get_repo_name_handles_trailing_slash(self):
        """Test handling of trailing slash in URL."""
        url = 'https://github.com/user/myrepo/'
        result = self.repo_manager.get_repo_name(url)
        self.assertEqual(result, 'myrepo')

    @patch('src.repo_manager.git.Repo.clone_from')
    def test_clone_repository_success(self, mock_clone):
        """Test successful repository cloning."""
        repo_url = 'https://github.com/user/test-repo.git'
        destination = Path('/tmp/test-repo')

        mock_clone.return_value = MagicMock()

        result = self.repo_manager.clone_repository(repo_url, destination)

        self.assertTrue(result)
        mock_clone.assert_called_once()

    @patch('src.repo_manager.git.Repo.clone_from')
    def test_clone_repository_with_proxy(self, mock_clone):
        """Test repository cloning with proxy configuration."""
        self.proxy_manager.set_proxy(
            http_proxy='http://proxy.example.com:8080',
            https_proxy='http://proxy.example.com:8080'
        )

        repo_url = 'https://github.com/user/test-repo.git'
        destination = Path('/tmp/test-repo')

        mock_clone.return_value = MagicMock()

        result = self.repo_manager.clone_repository(repo_url, destination)

        self.assertTrue(result)
        # Verify clone was called with environment variables
        call_kwargs = mock_clone.call_args[1]
        self.assertIn('env', call_kwargs)
        env = call_kwargs['env']
        self.assertEqual(env['http_proxy'], 'http://proxy.example.com:8080')

    @patch('src.repo_manager.git.Repo.clone_from')
    def test_clone_repository_failure(self, mock_clone):
        """Test handling of clone failure."""
        mock_clone.side_effect = Exception('Clone failed')

        repo_url = 'https://github.com/user/test-repo.git'
        destination = Path('/tmp/test-repo')

        result = self.repo_manager.clone_repository(repo_url, destination)

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
