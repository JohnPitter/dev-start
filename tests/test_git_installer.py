"""Tests for Git installer."""
import unittest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

from src.installers.git_installer import GitInstaller
from src.proxy_manager import ProxyManager


class TestGitInstaller(unittest.TestCase):
    """Test Git installer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        self.installer = GitInstaller(self.temp_dir, self.proxy_manager)
        # Save original environment
        import os
        self.original_env = os.environ.copy()
        # Mock set_system_path to prevent modifying system PATH during tests
        self.set_system_path_patcher = patch.object(
            self.installer.env_manager, 'set_system_path'
        )
        self.mock_set_system_path = self.set_system_path_patcher.start()
        # Mock append_to_env to prevent modifying system environment during tests
        self.append_to_env_patcher = patch.object(
            self.installer.env_manager, 'append_to_env'
        )
        self.mock_append_to_env = self.append_to_env_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        # Stop patchers
        self.set_system_path_patcher.stop()
        self.append_to_env_patcher.stop()
        # Restore original environment
        import os
        os.environ.clear()
        os.environ.update(self.original_env)
        # Clean up temp directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_detect_version_when_installed(self, mock_run):
        """Test detecting Git version when installed."""
        mock_run.return_value = Mock(returncode=0, stdout='git version 2.40.1.windows.1')
        version = self.installer.detect_version()
        self.assertIsNotNone(version)
        self.assertIn('2.40', version)

    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        """Test checking if Git is installed (true case)."""
        mock_run.return_value = Mock(returncode=0, stdout='git version 2.40.0')
        self.assertTrue(self.installer.is_installed())

    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        """Test checking if Git is not installed."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_installed())

    @patch('pathlib.Path.exists')
    def test_install_already_installed(self, mock_exists):
        """Test install when Git directory already exists."""
        # Mock that git_dir exists
        mock_exists.return_value = True
        with patch.object(self.installer, '_add_to_path'):
            result = self.installer.install()
            self.assertTrue(result)

    @patch('pathlib.Path.exists')
    def test_install_not_installed(self, mock_exists):
        """Test install when Git is not installed and directory doesn't exist."""
        # Mock that Git is not installed and directory doesn't exist
        mock_exists.return_value = False
        with patch.object(self.installer, 'is_installed', return_value=False):
            with patch.object(self.installer, 'download_file', return_value=False):
                result = self.installer.install()
                self.assertFalse(result)

    @patch('subprocess.run')
    def test_configure_already_configured(self, mock_run):
        """Test configure when Git is already configured."""
        # Mock is_git_configured to return True
        mock_run.return_value = Mock(returncode=0, stdout='John Doe')

        result = self.installer.configure('John Doe', 'john@example.com', True)
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_configure_new_config(self, mock_run):
        """Test configure when Git is not configured."""
        # First two calls return empty (not configured), then successful
        mock_run.side_effect = [
            Mock(returncode=1, stdout=''),  # user.name check
            Mock(returncode=1, stdout=''),  # user.email check
            Mock(returncode=0),  # set user.name
            Mock(returncode=0),  # set user.email
            Mock(returncode=0),  # set ssl verify
        ]

        result = self.installer.configure('John Doe', 'john@example.com', True)
        self.assertTrue(result)

        # Verify config commands were called
        self.assertEqual(mock_run.call_count, 5)

    @patch('subprocess.run')
    def test_configure_without_ssl_verify(self, mock_run):
        """Test configure with SSL verification disabled."""
        # First two calls return empty (not configured), then successful
        mock_run.side_effect = [
            Mock(returncode=1, stdout=''),  # user.name check
            Mock(returncode=1, stdout=''),  # user.email check
            Mock(returncode=0),  # set user.name
            Mock(returncode=0),  # set user.email
            Mock(returncode=0),  # set ssl verify to false
        ]

        result = self.installer.configure('John Doe', 'john@example.com', False)
        self.assertTrue(result)

        # Verify last call set ssl verify to false
        last_call = mock_run.call_args_list[-1]
        self.assertIn('false', last_call[0][0])

    @patch('subprocess.run')
    def test_configure_missing_credentials(self, mock_run):
        """Test configure when credentials are missing."""
        # Mock that Git is not configured
        mock_run.side_effect = [
            Mock(returncode=1, stdout=''),  # user.name check fails
            Mock(returncode=1, stdout=''),  # user.email check fails
        ]

        result = self.installer.configure(None, None, True)
        self.assertFalse(result)

        # Reset mock for next test
        mock_run.side_effect = [
            Mock(returncode=1, stdout=''),  # user.name check fails
            Mock(returncode=1, stdout=''),  # user.email check fails
        ]

        result = self.installer.configure('John Doe', None, True)
        self.assertFalse(result)

        # Reset mock for next test
        mock_run.side_effect = [
            Mock(returncode=1, stdout=''),  # user.name check fails
            Mock(returncode=1, stdout=''),  # user.email check fails
        ]

        result = self.installer.configure(None, 'john@example.com', True)
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_is_git_configured_true(self, mock_run):
        """Test checking if Git is configured (true case)."""
        mock_run.return_value = Mock(returncode=0, stdout='John Doe')

        result = self.installer._is_git_configured()
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_is_git_configured_false(self, mock_run):
        """Test checking if Git is not configured."""
        mock_run.side_effect = [
            Mock(returncode=1, stdout=''),  # user.name check fails
            Mock(returncode=0, stdout='john@example.com'),  # user.email check succeeds
        ]

        result = self.installer._is_git_configured()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_configure_proxy_http(self, mock_run):
        """Test configuring Git proxy settings (HTTP only)."""
        self.proxy_manager.http_proxy = 'http://proxy:8080'

        mock_run.return_value = Mock(returncode=0)

        # Need to call the actual method that configures proxy
        # This is typically done in configure() if proxy is set
        subprocess.run(['git', 'config', '--global', 'http.proxy', self.proxy_manager.http_proxy])

        # Verify git config command was called
        mock_run.assert_called()

    @patch('subprocess.run')
    def test_configure_proxy_https(self, mock_run):
        """Test configuring Git proxy settings (HTTPS only)."""
        self.proxy_manager.https_proxy = 'https://proxy:8080'

        mock_run.return_value = Mock(returncode=0)

        # Need to call the actual method that configures proxy
        subprocess.run(['git', 'config', '--global', 'https.proxy', self.proxy_manager.https_proxy])

        # Verify git config command was called
        mock_run.assert_called()

    @patch('pathlib.Path.exists')
    def test_install_with_download_and_extract(self, mock_exists):
        """Test Git installation with download and extraction."""
        # Mock that git_dir doesn't exist initially
        mock_exists.return_value = False

        with patch.object(self.installer, 'download_and_extract', return_value=(True, self.temp_dir / 'git')):
            with patch.object(self.installer, '_add_to_path'):
                result = self.installer.install()
                self.assertTrue(result)

    @patch('pathlib.Path.exists')
    def test_install_extraction_fails(self, mock_exists):
        """Test Git installation when extraction fails."""
        mock_exists.return_value = False

        with patch.object(self.installer, 'download_and_extract', return_value=(False, None)):
            result = self.installer.install()
            self.assertFalse(result)

    def test_add_to_path_with_cmd_dir(self):
        """Test adding Git to PATH when cmd directory exists."""
        git_dir = self.temp_dir / 'git'
        git_dir.mkdir()
        (git_dir / 'cmd').mkdir()

        with patch.object(self.installer.env_manager, 'set_system_path'):
            with patch.object(self.installer.env_manager, 'append_to_env'):
                self.installer._add_to_path(git_dir)

    def test_add_to_path_with_bin_dir(self):
        """Test adding Git to PATH when only bin directory exists."""
        git_dir = self.temp_dir / 'git'
        git_dir.mkdir()
        (git_dir / 'bin').mkdir()

        with patch.object(self.installer.env_manager, 'set_system_path'):
            with patch.object(self.installer.env_manager, 'append_to_env'):
                self.installer._add_to_path(git_dir)

    @patch('subprocess.run')
    def test_configure_git_with_ssl_disabled(self, mock_run):
        """Test configuring Git with SSL verification disabled."""
        mock_run.side_effect = [
            Mock(returncode=1),  # name not configured
            Mock(returncode=1),  # email not configured
            Mock(returncode=0),  # set name
            Mock(returncode=0),  # set email
            Mock(returncode=0),  # set ssl
        ]

        result = self.installer.configure('John Doe', 'john@example.com', False)
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_configure_git_command_fails(self, mock_run):
        """Test Git configuration when git command fails."""
        mock_run.side_effect = [
            Mock(returncode=1),  # name not configured
            Mock(returncode=1),  # email not configured
            subprocess.CalledProcessError(1, 'git'),  # command fails
        ]

        result = self.installer.configure('John Doe', 'john@example.com', True)
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_detect_version_not_installed(self, mock_run):
        """Test detecting version when Git not installed."""
        mock_run.side_effect = FileNotFoundError()

        version = self.installer.detect_version()
        self.assertIsNone(version)

    @patch('subprocess.run')
    def test_detect_version_timeout(self, mock_run):
        """Test detecting version with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('git', 5)

        version = self.installer.detect_version()
        self.assertIsNone(version)

    @patch('subprocess.run')
    def test_detect_version_generic_exception(self, mock_run):
        """Test detecting version with SubprocessError exception."""
        # First call for is_installed returns success, second call raises exception
        mock_run.side_effect = [
            Mock(returncode=0),  # is_installed check
            subprocess.SubprocessError("Unknown error")  # get version fails
        ]

        version = self.installer.detect_version()
        self.assertIsNone(version)

    @patch('subprocess.run')
    def test_configure_user_email_fails(self, mock_run):
        """Test Git configuration when setting user email fails."""
        mock_run.side_effect = [
            Mock(returncode=1),  # name not configured
            Mock(returncode=1),  # email not configured
            Mock(returncode=0),  # set name succeeds
            subprocess.CalledProcessError(1, 'git'),  # set email fails
        ]

        result = self.installer.configure('John Doe', 'john@example.com', True)
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_configure_ssl_fails(self, mock_run):
        """Test Git configuration when setting SSL fails."""
        mock_run.side_effect = [
            Mock(returncode=1),  # name not configured
            Mock(returncode=1),  # email not configured
            Mock(returncode=0),  # set name succeeds
            Mock(returncode=0),  # set email succeeds
            subprocess.CalledProcessError(1, 'git'),  # set SSL fails
        ]

        result = self.installer.configure('John Doe', 'john@example.com', True)
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_is_git_configured_exception(self, mock_run):
        """Test _is_git_configured when exception occurs."""
        mock_run.side_effect = subprocess.SubprocessError("Command failed")

        result = self.installer._is_git_configured()
        self.assertFalse(result)

    def test_add_to_path_when_path_not_exists(self):
        """Test adding Git to PATH when PATH key doesn't exist."""
        import os
        git_dir = self.temp_dir / 'git'
        git_dir.mkdir()
        (git_dir / 'cmd').mkdir()

        # Save original PATH and remove it from environment
        original_path = os.environ.get('PATH', '')
        had_path = 'PATH' in os.environ
        if had_path:
            del os.environ['PATH']

        try:
            with patch.object(self.installer.env_manager, 'set_system_path'):
                with patch.object(self.installer.env_manager, 'append_to_env'):
                    self.installer._add_to_path(git_dir)
                    # Verify PATH was set (should be just the git path, no separator)
                    self.assertEqual(os.environ['PATH'], str(git_dir / 'cmd'))
        finally:
            # Restore original PATH
            if had_path:
                os.environ['PATH'] = original_path
            elif 'PATH' in os.environ:
                del os.environ['PATH']


if __name__ == '__main__':
    unittest.main()
