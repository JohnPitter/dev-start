"""Git installer and verifier."""
import subprocess
from pathlib import Path
from typing import Optional

from .base import BaseInstaller
from ..constants import (
    DOWNLOAD_URLS,
    DOWNLOAD_CHECKSUMS,
    DEFAULT_VERSIONS,
    GIT_TIMEOUT,
    get_tools_dir,
)
from ..logger import get_logger

logger = get_logger(__name__)


class GitInstaller(BaseInstaller):
    """Installer for Git."""

    def detect_version(self) -> Optional[str]:
        """Get current Git version if installed."""
        if self.is_installed():
            try:
                result = subprocess.run(
                    ['git', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=GIT_TIMEOUT
                )
                if result.returncode == 0:
                    # Output format: "git version 2.43.0.windows.1"
                    return result.stdout.strip().split()[-1]
            except subprocess.TimeoutExpired:
                logger.warning("Git version check timed out")
            except FileNotFoundError:
                pass
            except subprocess.SubprocessError as e:
                logger.debug(f"Error getting git version: {e}")
        return None

    def is_installed(self) -> bool:
        """Check if Git is installed and accessible."""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=GIT_TIMEOUT
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self) -> bool:
        """Install Git for Windows."""
        logger.progress("Installing Git...")

        tools_dir = get_tools_dir()
        git_dir = tools_dir / 'git'
        version = DEFAULT_VERSIONS['git']

        if git_dir.exists():
            logger.info("Git directory already exists, adding to PATH...")
            self._add_to_path(git_dir)
            return True

        # Get download URL and checksum
        download_url = DOWNLOAD_URLS['git'].get(version)
        expected_checksum = DOWNLOAD_CHECKSUMS.get('git', {}).get(version)

        if not download_url:
            logger.error(f"No download URL for Git version {version}")
            return False

        logger.progress(f"Downloading Git {version}...")

        # Download and extract using base method
        success, extracted_dir = self.download_and_extract(
            download_url,
            git_dir,
            expected_checksum=expected_checksum
        )

        if not success:
            logger.error("Failed to download Git")
            logger.info("Please install Git manually from: https://git-scm.com/download/win")
            return False

        # Add to PATH
        self._add_to_path(git_dir)

        logger.success("Git installed successfully!")
        return True

    def _add_to_path(self, git_dir: Path) -> None:
        """Add Git to system PATH."""
        # Determine Git bin directory
        git_bin = git_dir / 'cmd'
        if git_bin.exists():
            git_path = str(git_bin)
        else:
            # MinGit structure
            git_path = str(git_dir / 'bin')

        git_home = str(git_dir)

        # Use base class method to setup environment
        self.setup_tool_environment('GIT', git_home, git_path)

    def configure(self, user_name: str = None, user_email: str = None, ssl_verify: bool = True) -> bool:
        """Configure Git (basic setup)."""
        logger.progress("Configuring Git...")

        # Check if Git is already configured
        if self._is_git_configured():
            logger.success("Git is already configured")
            return True

        # If parameters not provided, prompt user
        if not user_name or not user_email:
            logger.info("Git needs to be configured with your information")
            logger.info("This is required for committing code to repositories")
            return False  # Return False to indicate configuration is needed

        # Configure user name
        try:
            subprocess.run(['git', 'config', '--global', 'user.name', user_name], check=True)
            logger.success(f"Git user name set to: {user_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set Git user name", details=str(e))
            return False
        except FileNotFoundError:
            logger.error("Git command not found")
            return False

        # Configure user email
        try:
            subprocess.run(['git', 'config', '--global', 'user.email', user_email], check=True)
            logger.success(f"Git user email set to: {user_email}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set Git user email", details=str(e))
            return False

        # Configure SSL verification
        try:
            ssl_value = 'true' if ssl_verify else 'false'
            subprocess.run(['git', 'config', '--global', 'http.sslVerify', ssl_value], check=True)
            logger.success(f"Git SSL verification set to: {ssl_value}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set Git SSL verification", details=str(e))
            return False

        logger.success("Git configuration completed successfully")
        return True

    def _is_git_configured(self) -> bool:
        """Check if Git is already configured with user name and email."""
        try:
            name_result = subprocess.run(
                ['git', 'config', '--global', 'user.name'],
                capture_output=True,
                text=True
            )
            email_result = subprocess.run(
                ['git', 'config', '--global', 'user.email'],
                capture_output=True,
                text=True
            )
            return (name_result.returncode == 0 and
                    email_result.returncode == 0 and
                    name_result.stdout.strip() and
                    email_result.stdout.strip())
        except (FileNotFoundError, subprocess.SubprocessError):
            return False
