"""Tests for installers."""
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.proxy_manager import ProxyManager
from src.installers.base import BaseInstaller
from src.installers.git_installer import GitInstaller
from src.installers.python_installer import PythonInstaller
from src.installers.nodejs_installer import NodeJSInstaller


class TestInstaller(BaseInstaller):
    """Concrete test implementation of BaseInstaller for testing abstract methods."""

    def detect_version(self):
        """Test implementation."""
        pass

    def is_installed(self):
        """Test implementation."""
        pass

    def install(self):
        """Test implementation."""
        pass

    def configure(self):
        """Test implementation."""
        pass


class TestGitInstaller(unittest.TestCase):
    """Test cases for GitInstaller."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        self.installer = GitInstaller(self.temp_dir, self.proxy_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        """Test Git is installed detection."""
        mock_run.return_value = Mock(returncode=0, stdout='git version 2.43.0')
        self.assertTrue(self.installer.is_installed())

    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        """Test Git is not installed detection."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_installed())

    @patch('subprocess.run')
    def test_detect_version(self, mock_run):
        """Test Git version detection."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='git version 2.43.0.windows.1'
        )

        version = self.installer.detect_version()
        self.assertEqual(version, '2.43.0.windows.1')

    @patch('subprocess.run')
    def test_detect_version_not_installed(self, mock_run):
        """Test version detection when Git is not installed."""
        mock_run.side_effect = FileNotFoundError()
        version = self.installer.detect_version()
        self.assertIsNone(version)


class TestPythonInstaller(unittest.TestCase):
    """Test cases for PythonInstaller."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        self.installer = PythonInstaller(self.temp_dir, self.proxy_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        """Test Python is installed detection."""
        mock_run.return_value = Mock(returncode=0)
        self.assertTrue(self.installer.is_installed())

    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        """Test Python is not installed detection."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_installed())

    def test_detect_version_from_runtime_txt(self):
        """Test version detection from runtime.txt."""
        runtime_file = self.temp_dir / 'runtime.txt'
        runtime_file.write_text('python-3.11.5')

        version = self.installer.detect_version()
        self.assertEqual(version, '3.11.5')

    def test_detect_version_from_python_version(self):
        """Test version detection from .python-version."""
        version_file = self.temp_dir / '.python-version'
        version_file.write_text('3.10.8')

        version = self.installer.detect_version()
        self.assertEqual(version, '3.10.8')

    def test_detect_version_default(self):
        """Test default version when no version file exists."""
        version = self.installer.detect_version()
        self.assertEqual(version, '3.11')


class TestNodeJSInstaller(unittest.TestCase):
    """Test cases for NodeJSInstaller."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        self.installer = NodeJSInstaller(self.temp_dir, self.proxy_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        """Test Node.js is installed detection."""
        mock_run.return_value = Mock(returncode=0)
        self.assertTrue(self.installer.is_installed())

    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        """Test Node.js is not installed detection."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_installed())

    def test_detect_version_from_package_json(self):
        """Test version detection from package.json."""
        package_json = self.temp_dir / 'package.json'
        package_json.write_text('''
        {
            "name": "test-app",
            "engines": {
                "node": ">=18.0.0"
            }
        }
        ''')

        version = self.installer.detect_version()
        self.assertEqual(version, '18.0.0')

    def test_detect_version_default(self):
        """Test default version when no package.json exists."""
        version = self.installer.detect_version()
        self.assertEqual(version, '20.11.0')


class TestBaseInstaller(unittest.TestCase):
    """Test cases for BaseInstaller common functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        # Use GitInstaller as concrete implementation
        self.installer = GitInstaller(self.temp_dir, self.proxy_manager)
        # Create test installer for abstract method coverage
        self.test_installer = TestInstaller(self.temp_dir, self.proxy_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_abstract_methods(self):
        """Test abstract method implementations are called."""
        # Call abstract methods to ensure they're covered
        self.test_installer.detect_version()
        self.test_installer.is_installed()
        self.test_installer.install()
        self.test_installer.configure()

    @patch('requests.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'test data']
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        destination = self.temp_dir / 'downloads' / 'test.zip'
        result = self.installer.download_file('http://example.com/file.zip', destination)

        self.assertTrue(result)
        self.assertTrue(destination.exists())

    @patch('requests.get')
    def test_download_file_with_proxy(self, mock_get):
        """Test file download with proxy."""
        self.proxy_manager.set_proxy(http_proxy='http://proxy:8080')

        mock_response = Mock()
        mock_response.iter_content.return_value = [b'data']
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        destination = self.temp_dir / 'test.zip'
        result = self.installer.download_file('http://example.com/file.zip', destination)

        self.assertTrue(result)
        # Verify proxy was used
        call_kwargs = mock_get.call_args[1]
        self.assertIn('proxies', call_kwargs)

    @patch('requests.get')
    def test_download_file_failure(self, mock_get):
        """Test handling of download failure."""
        mock_get.side_effect = Exception('Network error')

        destination = self.temp_dir / 'test.zip'
        result = self.installer.download_file('http://example.com/file.zip', destination)

        self.assertFalse(result)

    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = Mock(returncode=0, stdout='Success', stderr='')

        success, output = self.installer.run_command(['echo', 'test'])

        self.assertTrue(success)
        self.assertIn('Success', output)

    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test command execution failure."""
        mock_run.return_value = Mock(returncode=1, stdout='', stderr='Error occurred')

        success, output = self.installer.run_command(['false'])

        self.assertFalse(success)
        self.assertIn('Error occurred', output)

    @patch('subprocess.run')
    def test_run_command_with_http_proxy(self, mock_run):
        """Test command execution with HTTP proxy."""
        self.proxy_manager.set_proxy(http_proxy='http://proxy:8080')
        mock_run.return_value = Mock(returncode=0, stdout='OK', stderr='')

        success, output = self.installer.run_command(['test'])

        self.assertTrue(success)
        # Verify HTTP_PROXY was set in environment
        call_kwargs = mock_run.call_args[1]
        self.assertIn('env', call_kwargs)
        self.assertEqual(call_kwargs['env']['HTTP_PROXY'], 'http://proxy:8080')

    @patch('subprocess.run')
    def test_run_command_with_https_proxy(self, mock_run):
        """Test command execution with HTTPS proxy."""
        self.proxy_manager.set_proxy(https_proxy='https://proxy:8080')
        mock_run.return_value = Mock(returncode=0, stdout='OK', stderr='')

        success, output = self.installer.run_command(['test'])

        self.assertTrue(success)
        # Verify HTTPS_PROXY was set in environment
        call_kwargs = mock_run.call_args[1]
        self.assertIn('env', call_kwargs)
        self.assertEqual(call_kwargs['env']['HTTPS_PROXY'], 'https://proxy:8080')

    @patch('subprocess.run')
    def test_run_command_with_both_proxies(self, mock_run):
        """Test command execution with both HTTP and HTTPS proxies."""
        self.proxy_manager.set_proxy(
            http_proxy='http://proxy:8080',
            https_proxy='https://proxy:8080'
        )
        mock_run.return_value = Mock(returncode=0, stdout='OK', stderr='')

        success, output = self.installer.run_command(['test'])

        self.assertTrue(success)
        # Verify both proxies were set
        call_kwargs = mock_run.call_args[1]
        self.assertEqual(call_kwargs['env']['HTTP_PROXY'], 'http://proxy:8080')
        self.assertEqual(call_kwargs['env']['HTTPS_PROXY'], 'https://proxy:8080')

    @patch('subprocess.run')
    def test_run_command_with_custom_cwd(self, mock_run):
        """Test command execution with custom working directory."""
        custom_cwd = self.temp_dir / 'subdir'
        custom_cwd.mkdir()

        mock_run.return_value = Mock(returncode=0, stdout='OK', stderr='')

        success, output = self.installer.run_command(['test'], cwd=custom_cwd)

        self.assertTrue(success)
        # Verify custom cwd was used
        call_kwargs = mock_run.call_args[1]
        self.assertEqual(call_kwargs['cwd'], custom_cwd)

    @patch('subprocess.run')
    def test_run_command_exception(self, mock_run):
        """Test command execution when exception occurs."""
        mock_run.side_effect = Exception('Command failed')

        success, output = self.installer.run_command(['test'])

        self.assertFalse(success)
        self.assertIn('Command failed', output)


if __name__ == '__main__':
    unittest.main()
