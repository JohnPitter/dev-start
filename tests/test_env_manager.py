"""Tests for environment manager."""
import unittest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import patch, Mock
from src.env_manager import EnvironmentManager


class TestEnvironmentManager(unittest.TestCase):
    """Test cases for EnvironmentManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.env_manager = EnvironmentManager(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_create_env_file(self):
        """Test creating .env file."""
        variables = {
            'DATABASE_URL': 'postgresql://localhost/testdb',
            'API_KEY': 'test-key-123',
            'DEBUG': 'true'
        }

        self.env_manager.create_env_file(variables)

        env_file = self.temp_dir / '.env'
        self.assertTrue(env_file.exists())

        content = env_file.read_text()
        self.assertIn('DATABASE_URL=postgresql://localhost/testdb', content)
        self.assertIn('API_KEY=test-key-123', content)
        self.assertIn('DEBUG=true', content)

    def test_append_to_env(self):
        """Test appending to .env file."""
        # Create initial file
        self.env_manager.create_env_file({'VAR1': 'value1'})

        # Append new variable
        self.env_manager.append_to_env('VAR2', 'value2')

        env_file = self.temp_dir / '.env'
        content = env_file.read_text()

        self.assertIn('VAR1=value1', content)
        self.assertIn('VAR2=value2', content)

    def test_append_to_nonexistent_env(self):
        """Test appending creates new file if it doesn't exist."""
        self.env_manager.append_to_env('NEW_VAR', 'new_value')

        env_file = self.temp_dir / '.env'
        self.assertTrue(env_file.exists())
        self.assertIn('NEW_VAR=new_value', env_file.read_text())

    def test_create_config_dir(self):
        """Test creating configuration directory."""
        config_dir = self.env_manager.create_config_dir('config')

        self.assertTrue(config_dir.exists())
        self.assertTrue(config_dir.is_dir())
        self.assertEqual(config_dir.name, 'config')

    def test_create_nested_config_dir(self):
        """Test creating nested configuration directory."""
        config_dir = self.env_manager.create_config_dir('config/nested/deep')

        self.assertTrue(config_dir.exists())
        self.assertTrue(config_dir.is_dir())

    def test_write_config_file(self):
        """Test writing configuration file."""
        content = '# Test configuration\nkey=value\n'
        self.env_manager.write_config_file('test.conf', content)

        config_file = self.temp_dir / 'test.conf'
        self.assertTrue(config_file.exists())
        self.assertEqual(config_file.read_text(), content)

    def test_write_config_file_in_subdir(self):
        """Test writing configuration file in subdirectory."""
        content = 'test: true\n'
        self.env_manager.write_config_file('app.yml', content, 'config')

        config_file = self.temp_dir / 'config' / 'app.yml'
        self.assertTrue(config_file.exists())
        self.assertEqual(config_file.read_text(), content)

    @patch('sys.platform', 'win32')
    @patch('subprocess.run')
    def test_append_to_env_windows_success(self, mock_run):
        """Test appending environment variable on Windows with success."""
        mock_run.return_value = Mock(returncode=0)

        self.env_manager.append_to_env('TEST_VAR', 'test_value')

        # Verify setx was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], 'setx')
        self.assertEqual(call_args[1], 'TEST_VAR')
        self.assertEqual(call_args[2], 'test_value')

    @patch('sys.platform', 'win32')
    @patch('subprocess.run')
    def test_append_to_env_windows_failure(self, mock_run):
        """Test appending environment variable on Windows with failure."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, 'setx')

        # Should not raise exception, just log warning
        self.env_manager.append_to_env('TEST_VAR', 'test_value')

        # Verify file was still created
        env_file = self.temp_dir / '.env'
        self.assertTrue(env_file.exists())

    @patch('sys.platform', 'win32')
    @patch('subprocess.run')
    def test_set_system_path_windows_success(self, mock_run):
        """Test setting system PATH on Windows with success."""
        # Mock PowerShell responses
        mock_run.side_effect = [
            Mock(returncode=0, stdout='C:\\existing\\path', stderr=''),  # Get current PATH
            Mock(returncode=0, stdout='', stderr=''),  # Set new PATH
        ]

        self.env_manager.set_system_path('C:\\new\\path')

        # Verify PowerShell was called twice
        self.assertEqual(mock_run.call_count, 2)

    @patch('sys.platform', 'win32')
    @patch('subprocess.run')
    def test_set_system_path_windows_already_exists(self, mock_run):
        """Test setting system PATH when path already exists."""
        # Mock PowerShell response with path already in PATH
        mock_run.return_value = Mock(
            returncode=0,
            stdout='C:\\existing\\path;C:\\new\\path',
            stderr=''
        )

        self.env_manager.set_system_path('C:\\new\\path')

        # Verify only one call (to get PATH, not to set it)
        self.assertEqual(mock_run.call_count, 1)

    @patch('sys.platform', 'win32')
    @patch('subprocess.run')
    def test_set_system_path_windows_failure(self, mock_run):
        """Test setting system PATH on Windows with failure."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, 'powershell')

        # Should not raise exception, just log warning
        self.env_manager.set_system_path('C:\\new\\path')

    @patch('sys.platform', 'linux')
    def test_append_to_env_non_windows(self):
        """Test append_to_env on non-Windows platform."""
        with patch.object(sys, 'platform', 'linux'):
            self.env_manager.append_to_env('TEST_VAR', 'test_value')

            # Should only create .env file, not call setx
            env_file = self.temp_dir / '.env'
            self.assertTrue(env_file.exists())

    @patch('sys.platform', 'linux')
    def test_set_system_path_non_windows(self):
        """Test set_system_path on non-Windows platform."""
        import os
        original_path = os.environ.get('PATH', '')

        self.env_manager.set_system_path('/new/path')

        # Should update current process PATH
        self.assertIn('/new/path', os.environ['PATH'])

        # Restore original PATH
        os.environ['PATH'] = original_path

    @patch('sys.platform', 'win32')
    @patch('subprocess.run')
    def test_set_system_path_preserves_existing_paths(self, mock_run):
        """Test that set_system_path preserves all existing PATH entries."""
        # Simulate a user PATH with multiple existing entries
        existing_paths = 'C:\\Program Files\\Git\\cmd;C:\\Windows\\System32;C:\\Users\\test\\bin'

        # Mock PowerShell responses
        mock_run.side_effect = [
            Mock(returncode=0, stdout=existing_paths, stderr=''),  # Get current PATH
            Mock(returncode=0, stdout='', stderr=''),  # Set new PATH
        ]

        new_path = 'C:\\dev-start\\tools\\java\\bin'
        self.env_manager.set_system_path(new_path)

        # Verify PowerShell was called twice
        self.assertEqual(mock_run.call_count, 2)

        # Get the second call (SetEnvironmentVariable)
        second_call = mock_run.call_args_list[1]
        powershell_command = str(second_call[0][0])

        # Extract the PATH value that was set
        # The command should contain the new path followed by all existing paths
        # Note: paths are escaped in the PowerShell command
        self.assertIn('dev-start', powershell_command)
        self.assertIn('java', powershell_command)
        # Verify that all existing paths are preserved
        self.assertIn('Program Files', powershell_command)
        self.assertIn('Git', powershell_command)
        self.assertIn('Windows', powershell_command)
        self.assertIn('System32', powershell_command)
        self.assertIn('Users', powershell_command)
        self.assertIn('test', powershell_command)


if __name__ == '__main__':
    unittest.main()
