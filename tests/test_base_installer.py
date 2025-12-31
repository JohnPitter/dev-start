"""Tests for base installer functionality."""
import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

from src.installers.base import BaseInstaller
from src.proxy_manager import ProxyManager


class ConcreteInstaller(BaseInstaller):
    """Concrete implementation of BaseInstaller for testing."""

    def detect_version(self):
        return "1.0.0"

    def is_installed(self):
        return True

    def install(self):
        return True

    def configure(self):
        return True


class TestBaseInstaller(unittest.TestCase):
    """Test cases for BaseInstaller."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        self.installer = ConcreteInstaller(self.temp_dir, self.proxy_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_add_to_current_path_new_path(self):
        """Test adding new path to current PATH."""
        original_path = os.environ.get('PATH', '')
        new_path = '/test/new/path'

        self.installer.add_to_current_path(new_path)

        self.assertIn(new_path, os.environ['PATH'])

        # Restore original PATH
        os.environ['PATH'] = original_path

    def test_add_to_current_path_existing_path(self):
        """Test adding existing path to current PATH (should not duplicate)."""
        original_path = os.environ.get('PATH', '')
        existing_path = original_path.split(os.pathsep)[0] if original_path else '/existing'

        if not original_path:
            os.environ['PATH'] = existing_path

        original_count = os.environ['PATH'].count(existing_path)
        self.installer.add_to_current_path(existing_path)
        new_count = os.environ['PATH'].count(existing_path)

        self.assertEqual(original_count, new_count)

        # Restore original PATH
        os.environ['PATH'] = original_path

    def test_set_current_env(self):
        """Test setting current environment variable."""
        var_name = 'TEST_DEV_START_VAR'
        var_value = 'test_value'

        self.installer.set_current_env(var_name, var_value)

        self.assertEqual(os.environ.get(var_name), var_value)

        # Clean up
        del os.environ[var_name]

    @patch('src.installers.base.requests.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '100'}
        mock_response.iter_content.return_value = [b'test content']
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        destination = self.temp_dir / 'test_file.txt'
        result = self.installer.download_file('https://example.com/file.txt', destination)

        self.assertTrue(result)
        self.assertTrue(destination.exists())

    @patch('src.installers.base.requests.get')
    def test_download_file_with_checksum_verification(self, mock_get):
        """Test file download with checksum verification."""
        import hashlib

        content = b'test content'
        expected_checksum = hashlib.sha256(content).hexdigest()

        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': str(len(content))}
        mock_response.iter_content.return_value = [content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        destination = self.temp_dir / 'test_file.txt'
        result = self.installer.download_file(
            'https://example.com/file.txt',
            destination,
            expected_checksum=expected_checksum
        )

        self.assertTrue(result)

    @patch('src.installers.base.requests.get')
    def test_download_file_checksum_mismatch(self, mock_get):
        """Test file download with checksum mismatch."""
        content = b'test content'
        wrong_checksum = 'wrong_checksum_value'

        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': str(len(content))}
        mock_response.iter_content.return_value = [content]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        destination = self.temp_dir / 'test_file.txt'
        result = self.installer.download_file(
            'https://example.com/file.txt',
            destination,
            expected_checksum=wrong_checksum
        )

        self.assertFalse(result)
        # File should be deleted after checksum failure
        self.assertFalse(destination.exists())

    @patch('src.installers.base.requests.get')
    def test_download_file_timeout(self, mock_get):
        """Test file download timeout handling."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.Timeout()

        destination = self.temp_dir / 'test_file.txt'
        result = self.installer.download_file('https://example.com/file.txt', destination)

        self.assertFalse(result)

    @patch('src.installers.base.requests.get')
    def test_download_file_http_error(self, mock_get):
        """Test file download HTTP error handling."""
        import requests.exceptions

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        destination = self.temp_dir / 'test_file.txt'
        result = self.installer.download_file('https://example.com/file.txt', destination)

        self.assertFalse(result)

    def test_run_command_success(self):
        """Test running command successfully."""
        if os.name == 'nt':
            cmd = ['cmd', '/c', 'echo', 'test']
        else:
            cmd = ['echo', 'test']

        success, output = self.installer.run_command(cmd)

        self.assertTrue(success)
        self.assertIn('test', output)

    def test_run_command_failure(self):
        """Test running command that fails."""
        if os.name == 'nt':
            cmd = ['cmd', '/c', 'exit', '1']
        else:
            cmd = ['false']

        success, output = self.installer.run_command(cmd)

        self.assertFalse(success)

    def test_run_command_not_found(self):
        """Test running command that doesn't exist."""
        cmd = ['nonexistent_command_12345']
        success, output = self.installer.run_command(cmd)

        self.assertFalse(success)

    def test_find_executable_in_path(self):
        """Test finding executable in PATH."""
        # py or cmd should be in PATH on Windows
        result = self.installer.find_executable('cmd')

        self.assertIsNotNone(result)

    def test_find_executable_not_found(self):
        """Test finding non-existent executable."""
        result = self.installer.find_executable('nonexistent_exe_12345')

        self.assertIsNone(result)

    def test_find_executable_in_search_paths(self):
        """Test finding executable in custom search paths."""
        # Create a test executable
        test_bin_dir = self.temp_dir / 'bin'
        test_bin_dir.mkdir()

        if os.name == 'nt':
            test_exe = test_bin_dir / 'test.cmd'
            test_exe.write_text('@echo off\necho test')
        else:
            test_exe = test_bin_dir / 'test'
            test_exe.write_text('#!/bin/bash\necho test')
            test_exe.chmod(0o755)

        result = self.installer.find_executable('test', [test_bin_dir])

        self.assertIsNotNone(result)
        self.assertIn('test', result)

    @patch('src.installers.base.BaseInstaller.download_file')
    def test_download_and_extract_success(self, mock_download):
        """Test download and extract ZIP file."""
        import zipfile

        # Create a test ZIP file
        zip_path = self.temp_dir / 'test.zip'
        extract_dir = self.temp_dir / 'extract'
        extract_dir.mkdir()

        # Create ZIP with content
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('test_dir/file.txt', 'test content')

        # Mock download to copy the ZIP file
        def download_side_effect(url, dest, expected_checksum=None):
            shutil.copy(zip_path, dest)
            return True

        mock_download.side_effect = download_side_effect

        success, extracted = self.installer.download_and_extract(
            'https://example.com/test.zip',
            extract_dir
        )

        self.assertTrue(success)

    @patch('src.installers.base.BaseInstaller.download_file')
    def test_download_and_extract_download_failure(self, mock_download):
        """Test download and extract with download failure."""
        mock_download.return_value = False

        extract_dir = self.temp_dir / 'extract'
        extract_dir.mkdir()

        success, extracted = self.installer.download_and_extract(
            'https://example.com/test.zip',
            extract_dir
        )

        self.assertFalse(success)
        self.assertIsNone(extracted)


class TestSetupToolEnvironment(unittest.TestCase):
    """Test cases for setup_tool_environment method."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        self.installer = ConcreteInstaller(self.temp_dir, self.proxy_manager)
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_setup_tool_environment_sets_home_var(self):
        """Test setup_tool_environment sets HOME variable."""
        with patch.object(self.installer.env_manager, 'append_to_env') as mock_append, \
             patch.object(self.installer.env_manager, 'set_system_path') as mock_set_path:
            self.installer.setup_tool_environment('TEST', '/home/path', '/bin/path')
            self.assertEqual(os.environ.get('TEST_HOME'), '/home/path')

    def test_setup_tool_environment_adds_to_path(self):
        """Test setup_tool_environment adds to PATH."""
        with patch.object(self.installer.env_manager, 'append_to_env') as mock_append, \
             patch.object(self.installer.env_manager, 'set_system_path') as mock_set_path:
            self.installer.setup_tool_environment('TEST', '/home/path', '/bin/path')
            self.assertIn('/bin/path', os.environ.get('PATH', ''))

    def test_setup_tool_environment_calls_env_manager(self):
        """Test setup_tool_environment calls env_manager methods."""
        with patch.object(self.installer.env_manager, 'append_to_env') as mock_append, \
             patch.object(self.installer.env_manager, 'set_system_path') as mock_set_path:
            self.installer.setup_tool_environment('TEST', '/home/path', '/bin/path')
            mock_append.assert_called_once_with('TEST_HOME', '/home/path')
            mock_set_path.assert_called_once_with('/bin/path')


if __name__ == '__main__':
    unittest.main()
