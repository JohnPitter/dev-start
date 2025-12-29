"""Environment and configuration manager."""
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Optional


class EnvironmentManager:
    """Manages environment variables and configuration files."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.env_file = project_path / '.env'

    def create_env_file(self, variables: Dict[str, str]):
        """
        Create .env file with specified variables.

        Args:
            variables: Dictionary of environment variables
        """
        with open(self.env_file, 'w', encoding='utf-8') as f:
            for key, value in variables.items():
                f.write(f"{key}={value}\n")

    def append_to_env(self, key: str, value: str):
        """Set a permanent user environment variable (Windows)."""
        # Update .env file for project
        mode = 'a' if self.env_file.exists() else 'w'
        with open(self.env_file, mode, encoding='utf-8') as f:
            f.write(f"{key}={value}\n")

        # Set permanent Windows user environment variable
        if sys.platform == 'win32':
            try:
                # Use setx command to set permanent user environment variable
                subprocess.run(['setx', key, value], check=True, capture_output=True)
                print(f"\n✓ Set permanent environment variable: {key}={value}")
            except Exception as e:
                print(f"\n⚠ Could not set permanent environment variable {key}: {e}")
                print(f"  Please manually add {key}={value} to your system environment variables")

    def set_system_path(self, path: str):
        """Add path to system PATH environment variable permanently (Windows)."""
        # Update current process PATH
        current_path = os.environ.get('PATH', '')
        if path not in current_path:
            os.environ['PATH'] = f"{path};{current_path}"

        # Add to permanent Windows user PATH
        if sys.platform == 'win32':
            try:
                # Get current user PATH from registry
                result = subprocess.run(
                    ['powershell', '-Command',
                     '[Environment]::GetEnvironmentVariable("Path", "User")'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                current_user_path = result.stdout.strip()

                # Check if path is already in user PATH
                if path not in current_user_path:
                    # Add to user PATH
                    new_path = f"{path};{current_user_path}" if current_user_path else path

                    # Set new user PATH
                    subprocess.run(
                        ['powershell', '-Command',
                         f'[Environment]::SetEnvironmentVariable("Path", "{new_path}", "User")'],
                        check=True,
                        capture_output=True
                    )
                    print(f"\n✓ Added to permanent PATH: {path}")
                    print(f"  Restart your terminal/IDE to use the new PATH")
                else:
                    print(f"\n✓ Path already in permanent PATH: {path}")
            except Exception as e:
                print(f"\n⚠ Could not add to permanent PATH: {e}")
                print(f"  Please manually add {path} to your system PATH variable")

    def create_config_dir(self, dir_name: str) -> Path:
        """Create a configuration directory."""
        config_dir = self.project_path / dir_name
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def write_config_file(self, file_name: str, content: str, config_dir: Optional[str] = None):
        """Write a configuration file."""
        if config_dir:
            file_path = self.project_path / config_dir / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            file_path = self.project_path / file_name

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
