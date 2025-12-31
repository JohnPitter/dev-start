"""Python installer."""
import subprocess
from pathlib import Path
from typing import Optional

from .base import BaseInstaller
from ..constants import (
    DOWNLOAD_URLS,
    DEFAULT_VERSIONS,
    BUILD_TIMEOUT,
)
from ..logger import get_logger

logger = get_logger(__name__)


class PythonInstaller(BaseInstaller):
    """Installer for Python projects."""

    def detect_version(self) -> Optional[str]:
        """Detect Python version from requirements or setup files."""
        # Check for version in various files
        for file_name in ['runtime.txt', '.python-version']:
            file_path = self.project_path / file_name
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding='utf-8').strip()
                    if content.startswith('python-'):
                        return content.replace('python-', '')
                    return content
                except IOError as e:
                    logger.warning(f"Failed to read {file_name}", details=str(e))

        return DEFAULT_VERSIONS['python']

    def is_installed(self) -> bool:
        """Check if Python is installed."""
        try:
            result = subprocess.run(['python', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def is_pip_installed(self) -> bool:
        """Check if pip is installed."""
        try:
            result = subprocess.run(['pip', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def install(self) -> bool:
        """Install Python if not present."""
        if self.is_installed():
            logger.info("Python is already installed")
            return True

        download_url = DOWNLOAD_URLS['python'].get(DEFAULT_VERSIONS['python'])
        logger.warning("Python installation requires manual setup")
        logger.info(f"Please download Python from: {download_url}")
        return False

    def configure(self) -> bool:
        """Configure Python project."""
        logger.progress("Configuring Python project...")

        # Check if pip is installed
        if not self.is_pip_installed():
            logger.warning("pip not found. Installing pip...")
            try:
                result = subprocess.run(
                    ['python', '-m', 'ensurepip', '--upgrade'],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.success("pip installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install pip", details=str(e))
                return False
            except FileNotFoundError:
                logger.error("Python command not found")
                return False
        else:
            logger.success("pip is already installed")

        # Ensure pip directories exist
        self._ensure_pip_directories()

        # Configure proxy for pip if needed
        if self.proxy_manager.http_proxy:
            self._configure_pip_proxy()

        # Create virtual environment
        venv_path = self.project_path / 'venv'
        if not venv_path.exists():
            logger.progress("Creating virtual environment...")
            success, output = self.run_command(['python', '-m', 'venv', 'venv'])
            if not success:
                logger.error(f"Failed to create virtual environment", details=output)
                return False
            logger.success("Virtual environment created")

        # Install dependencies
        requirements_file = self.project_path / 'requirements.txt'
        setup_py = self.project_path / 'setup.py'
        pyproject_toml = self.project_path / 'pyproject.toml'

        if requirements_file.exists() or setup_py.exists() or pyproject_toml.exists():
            logger.progress("Installing project dependencies with pip...")
            if not self._run_pip_install(venv_path):
                logger.warning("pip install failed, but continuing...")
                return True  # Don't fail the whole process

        # Create .env file template
        env_file = self.project_path / '.env'
        if not env_file.exists():
            self.env_manager.create_env_file({
                'PYTHONPATH': str(self.project_path),
                'ENV': 'development'
            })

        return True

    def _run_pip_install(self, venv_path: Path) -> bool:
        """Run pip install to download dependencies."""
        pip_executable = venv_path / 'Scripts' / 'pip.exe'
        requirements_file = self.project_path / 'requirements.txt'
        setup_py = self.project_path / 'setup.py'

        # Determine install command
        if requirements_file.exists():
            logger.progress("Running: pip install -r requirements.txt")
            cmd = [str(pip_executable), 'install', '-r', 'requirements.txt']
        elif setup_py.exists():
            logger.progress("Running: pip install -e .")
            cmd = [str(pip_executable), 'install', '-e', '.']
        else:
            logger.progress("Running: pip install .")
            cmd = [str(pip_executable), 'install', '.']

        # Add proxy if configured
        if self.proxy_manager.http_proxy:
            cmd.extend(['--proxy', self.proxy_manager.http_proxy])

        success, output = self.run_command(cmd, timeout=BUILD_TIMEOUT)

        if success:
            logger.success("pip dependencies installed successfully")
        else:
            logger.error("pip install failed")
            if output:
                logger.debug(f"Output: {output[:500]}")

        return success

    def _ensure_pip_directories(self) -> None:
        """Ensure pip directories exist."""
        pip_config_dir = Path.home() / 'pip'
        pip_config_dir.mkdir(exist_ok=True)
        logger.info(f"pip directory created/verified: {pip_config_dir}")

        # Create default pip.ini if it doesn't exist
        pip_config = pip_config_dir / 'pip.ini'
        if not pip_config.exists():
            default_config = """[global]
# pip configuration file
timeout = 60

[install]
# Install options
"""
            try:
                pip_config.write_text(default_config, encoding='utf-8')
                logger.success(f"Created pip.ini: {pip_config}")
            except IOError as e:
                logger.warning(f"Could not create pip.ini", details=str(e))

    def _configure_pip_proxy(self) -> None:
        """Configure pip proxy settings."""
        pip_config_dir = Path.home() / 'pip'
        pip_config_dir.mkdir(exist_ok=True)
        pip_config = pip_config_dir / 'pip.ini'

        config_content = f"""[global]
# pip configuration file
timeout = 60
proxy = {self.proxy_manager.http_proxy}

[install]
# Install options with proxy
"""
        try:
            pip_config.write_text(config_content, encoding='utf-8')
            logger.success("pip proxy configured in pip.ini")
        except IOError as e:
            logger.warning(f"Could not configure pip proxy", details=str(e))
