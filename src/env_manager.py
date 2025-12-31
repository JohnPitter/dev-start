"""Environment and configuration manager."""
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, Optional

from .constants import ENV_VAR_NAME_PATTERN
from .exceptions import InvalidEnvironmentVariableError, PathUpdateError, EnvironmentVariableError
from .logger import get_logger

logger = get_logger(__name__)


class EnvironmentManager:
    """Manages environment variables and configuration files."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.env_file = project_path / '.env'

    def validate_env_var_name(self, name: str) -> bool:
        """
        Validate an environment variable name.

        Args:
            name: Environment variable name to validate

        Returns:
            True if valid

        Raises:
            InvalidEnvironmentVariableError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise InvalidEnvironmentVariableError(name or '')

        if not re.match(ENV_VAR_NAME_PATTERN, name):
            raise InvalidEnvironmentVariableError(name)

        return True

    def create_env_file(self, variables: Dict[str, str]) -> None:
        """
        Create .env file with specified variables.

        Args:
            variables: Dictionary of environment variables

        Raises:
            InvalidEnvironmentVariableError: If any variable name is invalid
        """
        # Validate all variable names
        for key in variables.keys():
            self.validate_env_var_name(key)

        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                for key, value in variables.items():
                    f.write(f"{key}={value}\n")
            logger.success(f"Created .env file: {self.env_file}")
        except IOError as e:
            logger.error(f"Failed to create .env file", details=str(e))
            raise

    def append_to_env(self, key: str, value: str) -> None:
        """
        Set a permanent user environment variable (Windows).

        Args:
            key: Environment variable name
            value: Environment variable value

        Raises:
            InvalidEnvironmentVariableError: If key is invalid
        """
        self.validate_env_var_name(key)

        # Update .env file for project
        mode = 'a' if self.env_file.exists() else 'w'
        try:
            with open(self.env_file, mode, encoding='utf-8') as f:
                f.write(f"{key}={value}\n")
        except IOError as e:
            logger.warning(f"Could not update .env file", details=str(e))

        # Set permanent Windows user environment variable
        if sys.platform == 'win32':
            try:
                # Use setx command to set permanent user environment variable
                result = subprocess.run(
                    ['setx', key, value],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.success(f"Set permanent environment variable: {key}")
            except subprocess.CalledProcessError as e:
                logger.warning(
                    f"Could not set permanent environment variable: {key}",
                    details=f"Please manually add {key}={value} to your system environment variables"
                )
            except FileNotFoundError:
                logger.warning(
                    f"setx command not found",
                    details="Unable to set permanent environment variable"
                )

    def set_system_path(self, path: str) -> None:
        """
        Add path to system PATH environment variable permanently (Windows).

        Args:
            path: Path to add to system PATH
        """
        # Update current process PATH
        current_path = os.environ.get('PATH', '')
        if path not in current_path:
            os.environ['PATH'] = f"{path};{current_path}"
            logger.debug(f"Added to current process PATH: {path}")

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
                    # Add to user PATH (preserving existing paths)
                    new_path = f"{path};{current_user_path}" if current_user_path else path

                    # Set new user PATH using PowerShell with proper argument passing
                    powershell_script = f'''
$newPath = @"
{new_path}
"@
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")
'''
                    subprocess.run(
                        ['powershell', '-NoProfile', '-NonInteractive', '-Command', powershell_script],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    logger.success(f"Added to permanent PATH: {path}")
                    logger.info("Restart your terminal/IDE to use the new PATH")
                else:
                    logger.info(f"Path already in permanent PATH: {path}")

            except subprocess.CalledProcessError as e:
                logger.warning(
                    f"Could not add to permanent PATH",
                    details=f"Please manually add {path} to your system PATH variable"
                )
            except FileNotFoundError:
                logger.warning(
                    "PowerShell not found",
                    details="Unable to modify permanent PATH"
                )

    def create_config_dir(self, dir_name: str) -> Path:
        """
        Create a configuration directory.

        Args:
            dir_name: Name of the directory to create

        Returns:
            Path to the created directory
        """
        config_dir = self.project_path / dir_name
        config_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created config directory: {config_dir}")
        return config_dir

    def write_config_file(self, file_name: str, content: str, config_dir: Optional[str] = None) -> None:
        """
        Write a configuration file.

        Args:
            file_name: Name of the file to write
            content: Content to write
            config_dir: Optional subdirectory for the file
        """
        if config_dir:
            file_path = self.project_path / config_dir / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            file_path = self.project_path / file_name

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.debug(f"Created config file: {file_path}")
        except IOError as e:
            logger.error(f"Failed to write config file: {file_path}", details=str(e))
            raise
