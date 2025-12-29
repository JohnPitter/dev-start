"""Git installer and verifier."""
import subprocess
import zipfile
from pathlib import Path
from typing import Optional
from .base import BaseInstaller


class GitInstaller(BaseInstaller):
    """Installer for Git."""

    GIT_DOWNLOAD_URL = 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/MinGit-2.43.0-64-bit.zip'

    def detect_version(self) -> Optional[str]:
        """Get current Git version if installed."""
        if self.is_installed():
            try:
                result = subprocess.run(
                    ['git', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    # Output format: "git version 2.43.0.windows.1"
                    return result.stdout.strip().split()[-1]
            except Exception:
                pass
        return None

    def is_installed(self) -> bool:
        """Check if Git is installed and accessible."""
        try:
            result = subprocess.run(
                ['git', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def install(self) -> bool:
        """Install Git for Windows."""
        print("Installing Git...")

        tools_dir = Path.home() / '.dev-start' / 'tools'
        git_dir = tools_dir / 'git'

        if git_dir.exists():
            print("Git directory already exists, adding to PATH...")
            self._add_to_path(git_dir)
            return True

        print(f"Downloading Git from {self.GIT_DOWNLOAD_URL}...")
        zip_path = tools_dir / 'git.zip'

        if not self.download_file(self.GIT_DOWNLOAD_URL, zip_path):
            print("Failed to download Git.")
            print("Please install Git manually from: https://git-scm.com/download/win")
            return False

        try:
            print("Extracting Git...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(git_dir)

            zip_path.unlink()

            # Add to PATH
            self._add_to_path(git_dir)

            print("Git installed successfully!")
            return True

        except Exception as e:
            print(f"Failed to extract Git: {e}")
            return False

    def _add_to_path(self, git_dir: Path):
        """Add Git to system PATH."""
        import os

        # Determine Git bin directory
        git_bin = git_dir / 'cmd'
        if git_bin.exists():
            git_path = str(git_bin)
        else:
            # MinGit structure
            git_path = str(git_dir / 'bin')

        git_home = str(git_dir)

        # Set environment variables for persistence
        self.env_manager.set_system_path(git_path)
        self.env_manager.append_to_env('GIT_HOME', git_home)

        # Update current process environment
        os.environ['GIT_HOME'] = git_home
        if 'PATH' in os.environ:
            if git_path not in os.environ['PATH']:
                os.environ['PATH'] = f"{git_path}{os.pathsep}{os.environ['PATH']}"
        else:
            os.environ['PATH'] = git_path

        print("✓ Git environment variables configured")
        print(f"  GIT_HOME: {git_home}")
        print(f"  PATH: {git_path} (added)")

    def configure(self, user_name: str = None, user_email: str = None, ssl_verify: bool = True) -> bool:
        """Configure Git (basic setup)."""
        print("\nConfiguring Git...")

        # Check if Git is already configured
        if self._is_git_configured():
            print("✓ Git is already configured")
            return True

        # If parameters not provided, prompt user
        if not user_name or not user_email:
            print("\n⚙ Git needs to be configured with your information")
            print("This is required for committing code to repositories")
            return False  # Return False to indicate configuration is needed

        # Configure user name
        try:
            subprocess.run(['git', 'config', '--global', 'user.name', user_name], check=True)
            print(f"✓ Git user name set to: {user_name}")
        except Exception as e:
            print(f"✗ Failed to set Git user name: {e}")
            return False

        # Configure user email
        try:
            subprocess.run(['git', 'config', '--global', 'user.email', user_email], check=True)
            print(f"✓ Git user email set to: {user_email}")
        except Exception as e:
            print(f"✗ Failed to set Git user email: {e}")
            return False

        # Configure SSL verification
        try:
            ssl_value = 'true' if ssl_verify else 'false'
            subprocess.run(['git', 'config', '--global', 'http.sslVerify', ssl_value], check=True)
            print(f"✓ Git SSL verification set to: {ssl_value}")
        except Exception as e:
            print(f"✗ Failed to set Git SSL verification: {e}")
            return False

        print("✓ Git configuration completed successfully")
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
            return name_result.returncode == 0 and email_result.returncode == 0
        except Exception:
            return False
