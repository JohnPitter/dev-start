"""Python installer."""
import subprocess
from pathlib import Path
from typing import Optional
from .base import BaseInstaller


class PythonInstaller(BaseInstaller):
    """Installer for Python projects."""

    PYTHON_DOWNLOAD_URL = 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe'

    def detect_version(self) -> Optional[str]:
        """Detect Python version from requirements or setup files."""
        # Check for version in various files
        for file_name in ['runtime.txt', '.python-version']:
            file_path = self.project_path / file_name
            if file_path.exists():
                content = file_path.read_text().strip()
                if content.startswith('python-'):
                    return content.replace('python-', '')
                return content

        return '3.11'  # Default version

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
            print("Python is already installed.")
            return True

        print("Python installation requires manual setup.")
        print(f"Please download Python from: {self.PYTHON_DOWNLOAD_URL}")
        return False

    def configure(self) -> bool:
        """Configure Python project."""
        print("\nConfiguring Python project...")

        # Check if pip is installed
        if not self.is_pip_installed():
            print("\n⚠ pip not found. Installing pip...")
            try:
                subprocess.run(['python', '-m', 'ensurepip', '--upgrade'], check=True)
                print("\n✓ pip installed successfully")
            except Exception as e:
                print(f"\n✗ Failed to install pip: {e}")
                return False
        else:
            print("\n✓ pip is already installed")

        # Ensure pip directories exist
        self._ensure_pip_directories()

        # Configure proxy for pip if needed
        if self.proxy_manager.http_proxy:
            self._configure_pip_proxy()

        # Create virtual environment
        venv_path = self.project_path / 'venv'
        if not venv_path.exists():
            print("Creating virtual environment...")
            success, output = self.run_command(['python', '-m', 'venv', 'venv'])
            if not success:
                print(f"Failed to create virtual environment: {output}")
                return False

        # Install dependencies
        requirements_file = self.project_path / 'requirements.txt'
        setup_py = self.project_path / 'setup.py'
        pyproject_toml = self.project_path / 'pyproject.toml'

        if requirements_file.exists() or setup_py.exists() or pyproject_toml.exists():
            print("\nInstalling project dependencies with pip...")
            if not self._run_pip_install(venv_path):
                print("\n⚠ Warning: pip install failed, but continuing...")
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
        try:
            pip_executable = venv_path / 'Scripts' / 'pip.exe'
            requirements_file = self.project_path / 'requirements.txt'
            setup_py = self.project_path / 'setup.py'

            # Determine install command
            if requirements_file.exists():
                print("\nRunning: pip install -r requirements.txt")
                cmd = [str(pip_executable), 'install', '-r', 'requirements.txt']
            elif setup_py.exists():
                print("\nRunning: pip install -e .")
                cmd = [str(pip_executable), 'install', '-e', '.']
            else:
                print("\nRunning: pip install .")
                cmd = [str(pip_executable), 'install', '.']

            # Add proxy if configured
            if self.proxy_manager.http_proxy:
                cmd.extend(['--proxy', self.proxy_manager.http_proxy])

            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            if result.returncode == 0:
                print("\n✓ pip dependencies installed successfully")
                return True
            else:
                print(f"\n✗ pip install failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr[:500]}")  # Print first 500 chars
                return False
        except subprocess.TimeoutExpired:
            print("\n✗ pip install timed out after 10 minutes")
            return False
        except FileNotFoundError:
            print("\n✗ pip not found in virtual environment")
            return False
        except Exception as e:
            print(f"\n✗ Error running pip: {e}")
            return False

    def _ensure_pip_directories(self):
        """Ensure pip directories exist."""
        pip_config_dir = Path.home() / 'pip'
        pip_config_dir.mkdir(exist_ok=True)
        print(f"✓ pip directory created/verified: {pip_config_dir}")

        # Create default pip.ini if it doesn't exist
        pip_config = pip_config_dir / 'pip.ini'
        if not pip_config.exists():
            default_config = """[global]
# pip configuration file
timeout = 60

[install]
# Install options
"""
            with open(pip_config, 'w', encoding='utf-8') as f:
                f.write(default_config)
            print(f"✓ Created pip.ini: {pip_config}")

    def _configure_pip_proxy(self):
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
        with open(pip_config, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✓ pip proxy configured in pip.ini")
