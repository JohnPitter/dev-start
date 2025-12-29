"""Tests for Python installer."""
import unittest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from src.installers.python_installer import PythonInstaller
from src.proxy_manager import ProxyManager


class TestPythonInstaller(unittest.TestCase):
    """Test Python installer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        self.installer = PythonInstaller(self.temp_dir, self.proxy_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_detect_version_from_runtime_txt(self):
        """Test detecting Python version from runtime.txt."""
        runtime_file = self.temp_dir / 'runtime.txt'
        runtime_file.write_text('python-3.10.5', encoding='utf-8')

        version = self.installer.detect_version()
        self.assertEqual(version, '3.10.5')

    def test_detect_version_from_python_version_file(self):
        """Test detecting Python version from .python-version."""
        version_file = self.temp_dir / '.python-version'
        version_file.write_text('3.9.7', encoding='utf-8')

        version = self.installer.detect_version()
        self.assertEqual(version, '3.9.7')

    def test_detect_version_default(self):
        """Test default Python version when no config files exist."""
        version = self.installer.detect_version()
        self.assertEqual(version, '3.11')

    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        """Test checking if Python is installed (true case)."""
        mock_run.return_value = Mock(returncode=0, stdout='Python 3.11.7')
        self.assertTrue(self.installer.is_installed())

    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        """Test checking if Python is not installed."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_installed())

    @patch('subprocess.run')
    def test_is_pip_installed_true(self, mock_run):
        """Test checking if pip is installed (true case)."""
        mock_run.return_value = Mock(returncode=0, stdout='pip 23.0.1')
        self.assertTrue(self.installer.is_pip_installed())

    @patch('subprocess.run')
    def test_is_pip_installed_false(self, mock_run):
        """Test checking if pip is not installed."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_pip_installed())

    def test_install_already_installed(self):
        """Test install when Python is already installed."""
        with patch.object(self.installer, 'is_installed', return_value=True):
            result = self.installer.install()
            self.assertTrue(result)

    def test_install_not_installed(self):
        """Test install when Python is not installed (manual install required)."""
        with patch.object(self.installer, 'is_installed', return_value=False):
            result = self.installer.install()
            self.assertFalse(result)

    @patch('subprocess.run')
    def test_configure_pip_not_installed(self, mock_run):
        """Test configure when pip is not installed but successfully installed."""
        with patch.object(self.installer, 'is_pip_installed', return_value=False):
            mock_run.return_value = Mock(returncode=0)
            with patch.object(self.installer, '_ensure_pip_directories'):
                with patch.object(self.installer, 'run_command', return_value=(True, '')):
                    result = self.installer.configure()
                    self.assertTrue(result)

    def test_configure_pip_already_installed(self):
        """Test configure when pip is already installed."""
        with patch.object(self.installer, 'is_pip_installed', return_value=True):
            with patch.object(self.installer, '_ensure_pip_directories'):
                with patch.object(self.installer, 'run_command', return_value=(True, '')):
                    result = self.installer.configure()
                    self.assertTrue(result)

    def test_configure_with_requirements_txt(self):
        """Test configure with requirements.txt present."""
        # Create requirements.txt
        requirements_file = self.temp_dir / 'requirements.txt'
        requirements_file.write_text('requests==2.28.0', encoding='utf-8')

        with patch.object(self.installer, 'is_pip_installed', return_value=True):
            with patch.object(self.installer, '_ensure_pip_directories'):
                with patch.object(self.installer, '_run_pip_install', return_value=True):
                    with patch.object(self.installer, 'run_command', return_value=(True, '')):
                        result = self.installer.configure()
                        self.assertTrue(result)

    def test_ensure_pip_directories_creates_config(self):
        """Test ensuring pip directories creates pip.ini."""
        pip_config_dir = Path.home() / 'pip'
        pip_config = pip_config_dir / 'pip.ini'

        # Backup existing config
        if pip_config.exists():
            backup_content = pip_config.read_text(encoding='utf-8')
            pip_config.unlink()
        else:
            backup_content = None

        try:
            self.installer._ensure_pip_directories()
            self.assertTrue(pip_config_dir.exists())
            self.assertTrue(pip_config.exists())
        finally:
            # Restore original config
            if backup_content:
                pip_config.write_text(backup_content, encoding='utf-8')

    def test_configure_pip_proxy(self):
        """Test configuring pip proxy settings."""
        self.proxy_manager.http_proxy = 'http://proxy:8080'

        pip_config_dir = Path.home() / 'pip'
        pip_config = pip_config_dir / 'pip.ini'

        # Backup existing config
        if pip_config.exists():
            backup_content = pip_config.read_text(encoding='utf-8')
        else:
            backup_content = None

        try:
            self.installer._configure_pip_proxy()
            self.assertTrue(pip_config.exists())

            content = pip_config.read_text(encoding='utf-8')
            self.assertIn('proxy = http://proxy:8080', content)
        finally:
            # Restore original config
            if backup_content:
                pip_config.write_text(backup_content, encoding='utf-8')
            elif pip_config.exists():
                pip_config.unlink()

    @patch('subprocess.run')
    def test_run_pip_install_with_requirements(self, mock_run):
        """Test running pip install with requirements.txt."""
        # Create venv and requirements.txt
        venv_path = self.temp_dir / 'venv'
        venv_path.mkdir()
        (venv_path / 'Scripts').mkdir()
        pip_exe = venv_path / 'Scripts' / 'pip.exe'
        pip_exe.write_text('', encoding='utf-8')

        requirements_file = self.temp_dir / 'requirements.txt'
        requirements_file.write_text('requests', encoding='utf-8')

        mock_run.return_value = Mock(returncode=0, stderr='')
        result = self.installer._run_pip_install(venv_path)
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_run_pip_install_failure(self, mock_run):
        """Test running pip install with failure."""
        # Create venv
        venv_path = self.temp_dir / 'venv'
        venv_path.mkdir()
        (venv_path / 'Scripts').mkdir()
        pip_exe = venv_path / 'Scripts' / 'pip.exe'
        pip_exe.write_text('', encoding='utf-8')

        requirements_file = self.temp_dir / 'requirements.txt'
        requirements_file.write_text('requests', encoding='utf-8')

        mock_run.return_value = Mock(returncode=1, stderr='Error: Package not found')
        result = self.installer._run_pip_install(venv_path)
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_run_pip_install_timeout(self, mock_run):
        """Test running pip install with timeout."""
        # Create venv
        venv_path = self.temp_dir / 'venv'
        venv_path.mkdir()
        (venv_path / 'Scripts').mkdir()
        pip_exe = venv_path / 'Scripts' / 'pip.exe'
        pip_exe.write_text('', encoding='utf-8')

        requirements_file = self.temp_dir / 'requirements.txt'
        requirements_file.write_text('requests', encoding='utf-8')

        mock_run.side_effect = subprocess.TimeoutExpired('pip', 600)
        result = self.installer._run_pip_install(venv_path)
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_run_pip_install_not_found(self, mock_run):
        """Test running pip install when pip not found."""
        venv_path = self.temp_dir / 'venv'
        venv_path.mkdir()

        requirements_file = self.temp_dir / 'requirements.txt'
        requirements_file.write_text('requests', encoding='utf-8')

        result = self.installer._run_pip_install(venv_path)
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_configure_pip_install_fails(self, mock_run):
        """Test configure when pip installation fails."""
        with patch.object(self.installer, 'is_pip_installed', return_value=False):
            mock_run.side_effect = Exception("Failed to install pip")
            result = self.installer.configure()
            self.assertFalse(result)

    def test_configure_with_proxy(self):
        """Test configure when proxy is set."""
        self.proxy_manager.http_proxy = 'http://proxy:8080'

        with patch.object(self.installer, 'is_pip_installed', return_value=True):
            with patch.object(self.installer, '_ensure_pip_directories'):
                with patch.object(self.installer, '_configure_pip_proxy') as mock_proxy:
                    with patch.object(self.installer, 'run_command', return_value=(True, '')):
                        result = self.installer.configure()
                        self.assertTrue(result)
                        mock_proxy.assert_called_once()

    def test_configure_venv_creation_fails(self):
        """Test configure when venv creation fails."""
        with patch.object(self.installer, 'is_pip_installed', return_value=True):
            with patch.object(self.installer, '_ensure_pip_directories'):
                with patch.object(self.installer, 'run_command', return_value=(False, 'venv creation failed')):
                    result = self.installer.configure()
                    self.assertFalse(result)

    def test_configure_pip_install_fails_but_continues(self):
        """Test configure when pip install fails but continues."""
        # Create requirements.txt
        requirements_file = self.temp_dir / 'requirements.txt'
        requirements_file.write_text('requests==2.28.0', encoding='utf-8')

        with patch.object(self.installer, 'is_pip_installed', return_value=True):
            with patch.object(self.installer, '_ensure_pip_directories'):
                with patch.object(self.installer, '_run_pip_install', return_value=False):
                    with patch.object(self.installer, 'run_command', return_value=(True, '')):
                        result = self.installer.configure()
                        # Should return True even though pip install failed
                        self.assertTrue(result)

    @patch('subprocess.run')
    def test_run_pip_install_with_setup_py(self, mock_run):
        """Test running pip install with setup.py."""
        # Create venv and setup.py
        venv_path = self.temp_dir / 'venv'
        venv_path.mkdir()
        (venv_path / 'Scripts').mkdir()
        pip_exe = venv_path / 'Scripts' / 'pip.exe'
        pip_exe.write_text('', encoding='utf-8')

        setup_file = self.temp_dir / 'setup.py'
        setup_file.write_text('from setuptools import setup', encoding='utf-8')

        mock_run.return_value = Mock(returncode=0, stderr='')
        result = self.installer._run_pip_install(venv_path)
        self.assertTrue(result)
        # Verify pip install -e . was called
        call_args = mock_run.call_args[0][0]
        self.assertIn('-e', call_args)

    @patch('subprocess.run')
    def test_run_pip_install_with_pyproject_toml(self, mock_run):
        """Test running pip install with pyproject.toml."""
        # Create venv and pyproject.toml
        venv_path = self.temp_dir / 'venv'
        venv_path.mkdir()
        (venv_path / 'Scripts').mkdir()
        pip_exe = venv_path / 'Scripts' / 'pip.exe'
        pip_exe.write_text('', encoding='utf-8')

        pyproject_file = self.temp_dir / 'pyproject.toml'
        pyproject_file.write_text('[tool.poetry]', encoding='utf-8')

        mock_run.return_value = Mock(returncode=0, stderr='')
        result = self.installer._run_pip_install(venv_path)
        self.assertTrue(result)
        # Verify pip install . was called
        call_args = mock_run.call_args[0][0]
        self.assertIn('install', call_args)

    @patch('subprocess.run')
    def test_run_pip_install_with_proxy(self, mock_run):
        """Test running pip install with proxy configured."""
        self.proxy_manager.http_proxy = 'http://proxy:8080'

        # Create venv and requirements.txt
        venv_path = self.temp_dir / 'venv'
        venv_path.mkdir()
        (venv_path / 'Scripts').mkdir()
        pip_exe = venv_path / 'Scripts' / 'pip.exe'
        pip_exe.write_text('', encoding='utf-8')

        requirements_file = self.temp_dir / 'requirements.txt'
        requirements_file.write_text('requests', encoding='utf-8')

        mock_run.return_value = Mock(returncode=0, stderr='')
        result = self.installer._run_pip_install(venv_path)
        self.assertTrue(result)
        # Verify --proxy was added to command
        call_args = mock_run.call_args[0][0]
        self.assertIn('--proxy', call_args)
        self.assertIn('http://proxy:8080', call_args)

    @patch('subprocess.run')
    def test_run_pip_install_file_not_found(self, mock_run):
        """Test running pip install when subprocess raises FileNotFoundError."""
        # Create venv
        venv_path = self.temp_dir / 'venv'
        venv_path.mkdir()
        (venv_path / 'Scripts').mkdir()
        pip_exe = venv_path / 'Scripts' / 'pip.exe'
        pip_exe.write_text('', encoding='utf-8')

        requirements_file = self.temp_dir / 'requirements.txt'
        requirements_file.write_text('requests', encoding='utf-8')

        mock_run.side_effect = FileNotFoundError("pip not found")
        result = self.installer._run_pip_install(venv_path)
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_run_pip_install_generic_exception(self, mock_run):
        """Test running pip install with generic exception."""
        # Create venv
        venv_path = self.temp_dir / 'venv'
        venv_path.mkdir()
        (venv_path / 'Scripts').mkdir()
        pip_exe = venv_path / 'Scripts' / 'pip.exe'
        pip_exe.write_text('', encoding='utf-8')

        requirements_file = self.temp_dir / 'requirements.txt'
        requirements_file.write_text('requests', encoding='utf-8')

        mock_run.side_effect = Exception("Unknown error")
        result = self.installer._run_pip_install(venv_path)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
