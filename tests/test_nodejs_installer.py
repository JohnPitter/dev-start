"""Tests for Node.js installer."""
import unittest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import json

from src.installers.nodejs_installer import NodeJSInstaller
from src.proxy_manager import ProxyManager


class TestNodeJSInstaller(unittest.TestCase):
    """Test Node.js installer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        self.installer = NodeJSInstaller(self.temp_dir, self.proxy_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_detect_version_from_package_json(self):
        """Test detecting Node.js version from package.json."""
        package_json = {
            "name": "test-project",
            "engines": {
                "node": ">=18.0.0"
            }
        }
        package_file = self.temp_dir / 'package.json'
        package_file.write_text(json.dumps(package_json), encoding='utf-8')

        version = self.installer.detect_version()
        self.assertEqual(version, '18.0.0')

    def test_detect_version_default(self):
        """Test default Node.js version when no package.json exists."""
        version = self.installer.detect_version()
        self.assertEqual(version, '20.11.0')

    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        """Test checking if Node.js is installed (true case)."""
        mock_run.return_value = Mock(returncode=0, stdout='v20.11.0')
        self.assertTrue(self.installer.is_installed())

    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        """Test checking if Node.js is not installed."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_installed())

    @patch('subprocess.run')
    def test_is_npm_installed_true(self, mock_run):
        """Test checking if npm is installed (true case)."""
        mock_run.return_value = Mock(returncode=0, stdout='9.5.0')
        self.assertTrue(self.installer.is_npm_installed())

    @patch('subprocess.run')
    def test_is_npm_installed_false(self, mock_run):
        """Test checking if npm is not installed."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_npm_installed())

    def test_install_already_installed(self):
        """Test install when Node.js is already installed."""
        with patch.object(self.installer, 'is_installed', return_value=True):
            result = self.installer.install()
            self.assertTrue(result)

    def test_configure_npm_not_found(self):
        """Test configure when npm is not found."""
        with patch.object(self.installer, 'is_npm_installed', return_value=False):
            result = self.installer.configure()
            self.assertFalse(result)

    def test_configure_with_package_json(self):
        """Test configure with package.json present."""
        # Create package.json
        package_file = self.temp_dir / 'package.json'
        package_file.write_text('{"name": "test"}', encoding='utf-8')

        with patch.object(self.installer, 'is_npm_installed', return_value=True):
            with patch.object(self.installer, '_run_npm_install', return_value=True):
                with patch.object(self.installer, '_ensure_npm_config'):
                    result = self.installer.configure()
                    self.assertTrue(result)

    def test_configure_no_package_json(self):
        """Test configure when no package.json exists."""
        with patch.object(self.installer, 'is_npm_installed', return_value=True):
            with patch.object(self.installer, '_ensure_npm_config'):
                result = self.installer.configure()
                self.assertTrue(result)

    def test_ensure_npm_config_creates_npmrc(self):
        """Test ensuring npm config creates .npmrc file."""
        npmrc_file = Path.home() / '.npmrc'

        # Remove existing .npmrc if it exists
        if npmrc_file.exists():
            backup_content = npmrc_file.read_text(encoding='utf-8')
            npmrc_file.unlink()
        else:
            backup_content = None

        try:
            self.installer._ensure_npm_config()
            self.assertTrue(npmrc_file.exists())
        finally:
            # Restore original .npmrc
            if backup_content:
                npmrc_file.write_text(backup_content, encoding='utf-8')

    @patch('subprocess.run')
    def test_configure_npm_proxy(self, mock_run):
        """Test configuring npm proxy settings."""
        self.proxy_manager.http_proxy = 'http://proxy:8080'
        self.proxy_manager.https_proxy = 'https://proxy:8080'

        self.installer._configure_npm_proxy()

        # Verify npm config commands were called
        self.assertEqual(mock_run.call_count, 2)

    @patch('subprocess.run')
    def test_run_npm_install_success(self, mock_run):
        """Test running npm install successfully."""
        # Create package.json
        package_file = self.temp_dir / 'package.json'
        package_file.write_text('{"name": "test"}', encoding='utf-8')

        mock_run.return_value = Mock(returncode=0, stdout='', stderr='')
        result = self.installer._run_npm_install()
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_run_npm_install_failure(self, mock_run):
        """Test running npm install with failure."""
        # Create package.json
        package_file = self.temp_dir / 'package.json'
        package_file.write_text('{"name": "test"}', encoding='utf-8')

        mock_run.return_value = Mock(returncode=1, stdout='', stderr='Error: Package not found')
        result = self.installer._run_npm_install()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_run_npm_install_timeout(self, mock_run):
        """Test running npm install with timeout."""
        # Create package.json
        package_file = self.temp_dir / 'package.json'
        package_file.write_text('{"name": "test"}', encoding='utf-8')

        mock_run.side_effect = subprocess.TimeoutExpired('npm', 600)
        result = self.installer._run_npm_install()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_run_npm_install_not_found(self, mock_run):
        """Test running npm install when npm not found."""
        # Create package.json
        package_file = self.temp_dir / 'package.json'
        package_file.write_text('{"name": "test"}', encoding='utf-8')

        mock_run.side_effect = FileNotFoundError()
        result = self.installer._run_npm_install()
        self.assertFalse(result)

    def test_detect_version_exception(self):
        """Test detecting version when exception occurs parsing package.json."""
        # Create invalid package.json
        package_file = self.temp_dir / 'package.json'
        package_file.write_text('invalid json{', encoding='utf-8')

        version = self.installer.detect_version()
        self.assertEqual(version, '20.11.0')  # Should return default

    @patch('pathlib.Path.exists')
    def test_install_with_download_and_extract(self, mock_exists):
        """Test Node.js installation with download and extraction."""
        mock_exists.return_value = False
        nodejs_dir = self.temp_dir / 'nodejs'

        with patch.object(self.installer, 'is_installed', return_value=False):
            with patch.object(self.installer, 'download_and_extract', return_value=(True, nodejs_dir)):
                with patch.object(self.installer, 'setup_tool_environment'):
                    result = self.installer.install()
                    self.assertTrue(result)

    @patch('pathlib.Path.exists')
    def test_install_download_fails(self, mock_exists):
        """Test Node.js installation when download fails."""
        mock_exists.return_value = False

        with patch.object(self.installer, 'is_installed', return_value=False):
            with patch.object(self.installer, 'download_file', return_value=False):
                result = self.installer.install()
                self.assertFalse(result)

    @patch('pathlib.Path.exists')
    def test_install_with_path_not_exists(self, mock_exists):
        """Test Node.js installation when PATH environment variable doesn't exist."""
        import os

        mock_exists.return_value = False
        nodejs_dir = self.temp_dir / 'nodejs'

        # Save and remove PATH
        original_path = os.environ.get('PATH', '')
        had_path = 'PATH' in os.environ
        if had_path:
            del os.environ['PATH']

        try:
            with patch.object(self.installer, 'is_installed', return_value=False):
                with patch.object(self.installer, 'download_and_extract', return_value=(True, nodejs_dir)):
                    with patch.object(self.installer, 'setup_tool_environment'):
                        result = self.installer.install()
                        self.assertTrue(result)
        finally:
            # Restore PATH
            if had_path:
                os.environ['PATH'] = original_path
            elif 'PATH' in os.environ:
                del os.environ['PATH']

    def test_configure_with_proxy(self):
        """Test configure when proxy is set."""
        self.proxy_manager.http_proxy = 'http://proxy:8080'

        with patch.object(self.installer, 'is_npm_installed', return_value=True):
            with patch.object(self.installer, '_configure_npm_proxy') as mock_proxy:
                with patch.object(self.installer, '_ensure_npm_config'):
                    result = self.installer.configure()
                    self.assertTrue(result)
                    mock_proxy.assert_called_once()

    def test_configure_npm_install_fails_but_continues(self):
        """Test configure when npm install fails but continues."""
        # Create package.json
        package_file = self.temp_dir / 'package.json'
        package_file.write_text('{"name": "test"}', encoding='utf-8')

        with patch.object(self.installer, 'is_npm_installed', return_value=True):
            with patch.object(self.installer, '_run_npm_install', return_value=False):
                with patch.object(self.installer, '_ensure_npm_config'):
                    result = self.installer.configure()
                    # Should return True even though npm install failed
                    self.assertTrue(result)

    @patch('subprocess.run')
    def test_run_npm_install_generic_exception(self, mock_run):
        """Test running npm install with SubprocessError."""
        # Create package.json
        package_file = self.temp_dir / 'package.json'
        package_file.write_text('{"name": "test"}', encoding='utf-8')

        mock_run.side_effect = subprocess.SubprocessError("Unknown error")
        result = self.installer._run_npm_install()
        self.assertFalse(result)

    def test_ensure_npm_config_already_exists(self):
        """Test ensuring npm config when .npmrc already exists."""
        npmrc_file = Path.home() / '.npmrc'

        # Ensure .npmrc exists
        if not npmrc_file.exists():
            npmrc_file.write_text('[global]\n', encoding='utf-8')
            cleanup_needed = True
        else:
            cleanup_needed = False

        try:
            # Should not raise error when file exists
            self.installer._ensure_npm_config()
            self.assertTrue(npmrc_file.exists())
        finally:
            if cleanup_needed and npmrc_file.exists():
                npmrc_file.unlink()


if __name__ == '__main__':
    unittest.main()
