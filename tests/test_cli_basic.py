"""Basic tests for CLI module."""
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

from src.cli import DevStartCLI


class TestCLIBasic(unittest.TestCase):
    """Test CLI basic functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cli = DevStartCLI()

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_cli_initialization(self):
        """Test CLI initializes correctly."""
        self.assertIsNotNone(self.cli.proxy_manager)
        self.assertIsNotNone(self.cli.repo_manager)
        self.assertIsNotNone(self.cli.detector)
        self.assertTrue(self.cli.base_dir.exists())

    def test_setup_proxy_http(self):
        """Test setting up HTTP proxy."""
        self.cli.setup_proxy(http_proxy='http://proxy:8080')
        self.assertEqual(self.cli.proxy_manager.http_proxy, 'http://proxy:8080')

    def test_setup_proxy_https(self):
        """Test setting up HTTPS proxy."""
        self.cli.setup_proxy(https_proxy='https://proxy:8080')
        self.assertEqual(self.cli.proxy_manager.https_proxy, 'https://proxy:8080')

    def test_setup_proxy_both(self):
        """Test setting up both HTTP and HTTPS proxy."""
        self.cli.setup_proxy(http_proxy='http://proxy:8080', https_proxy='https://proxy:8080')
        self.assertEqual(self.cli.proxy_manager.http_proxy, 'http://proxy:8080')
        self.assertEqual(self.cli.proxy_manager.https_proxy, 'https://proxy:8080')

    def test_remove_readonly(self):
        """Test readonly file handler."""
        # Create a test file
        test_file = self.temp_dir / 'test.txt'
        test_file.write_text('test content', encoding='utf-8')
        test_path = str(test_file)

        # Create a test function
        mock_func = Mock()

        # Call remove_readonly
        self.cli.remove_readonly(mock_func, test_path, None)

        # Verify function was called
        mock_func.assert_called_once_with(test_path)

    @patch('subprocess.run')
    def test_ensure_git_installed_already_installed(self, mock_run):
        """Test Git check when already installed."""
        mock_run.return_value = Mock(returncode=0, stdout='git version 2.40.0')
        result = self.cli.ensure_git_installed()
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
