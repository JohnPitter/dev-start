"""Command-line interface for dev-start."""
import click
import os
import stat
import time
import shutil
from pathlib import Path

from .constants import (
    get_base_dir,
    MAX_RMTREE_RETRIES,
    RETRY_DELAY_SECONDS,
)
from .exceptions import (
    DevStartError,
    InvalidURLError,
    CloneError,
    UnknownTechnologyError,
    InstallationError,
    ConfigurationError,
    RollbackError,
)
from .logger import get_logger
from .proxy_manager import ProxyManager
from .repo_manager import RepositoryManager
from .detector import TechnologyDetector, Technology
from .installers.git_installer import GitInstaller
from .installers.java_installer import JavaInstaller
from .installers.python_installer import PythonInstaller
from .installers.nodejs_installer import NodeJSInstaller

logger = get_logger(__name__)


class DevStartCLI:
    """Main CLI application."""

    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.repo_manager = RepositoryManager(self.proxy_manager)
        self.detector = TechnologyDetector()
        self.base_dir = get_base_dir()
        self.base_dir.mkdir(exist_ok=True)
        self.git_installer = None
        self._rollback_path = None  # Track path for rollback

    def setup_proxy(self, http_proxy: str = None, https_proxy: str = None) -> None:
        """Configure proxy settings."""
        if http_proxy or https_proxy:
            logger.progress("Configuring proxy settings...")
            try:
                self.proxy_manager.set_proxy(http_proxy, https_proxy)
                logger.success("Proxy configured")
            except DevStartError as e:
                logger.error(str(e))
                raise

    def remove_readonly(self, func, path, excinfo) -> None:
        """Error handler for shutil.rmtree to handle read-only files."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def safe_rmtree(self, path: str, max_retries: int = MAX_RMTREE_RETRIES) -> bool:
        """Safely remove directory tree with retry logic for locked files."""
        for attempt in range(max_retries):
            try:
                if os.path.exists(path):
                    shutil.rmtree(path, onerror=self.remove_readonly)
                    logger.success("Removed existing directory")
                    return True
                return True  # Directory doesn't exist, that's fine
            except PermissionError as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries}: Directory is locked, retrying..."
                    )
                    time.sleep(RETRY_DELAY_SECONDS)
                else:
                    logger.error(f"Failed to remove directory after {max_retries} attempts")
                    logger.info(f"Please close any programs using files in: {path}")
                    logger.info("Then manually delete the directory and try again")
                    return False
            except OSError as e:
                logger.error(f"Error removing directory", details=str(e))
                return False
        return False

    def _rollback(self, repo_path: Path) -> None:
        """Rollback a partial installation by removing the cloned repository."""
        if repo_path and repo_path.exists():
            logger.warning("Rolling back partial installation...")
            try:
                self.safe_rmtree(str(repo_path))
                logger.info("Rollback completed - repository removed")
            except Exception as e:
                logger.error(f"Rollback failed", details=str(e))
                raise RollbackError(str(e))

    def ensure_git_installed(self) -> bool:
        """Ensure Git is installed before processing repositories."""
        logger.section("Git Installation Check")

        # Create Git installer instance
        self.git_installer = GitInstaller(self.base_dir, self.proxy_manager)

        if self.git_installer.is_installed():
            version = self.git_installer.detect_version()
            logger.success(f"Git is installed (version {version})")

            # Check if Git needs configuration
            if not self.git_installer._is_git_configured():
                logger.warning("Git is not configured")
                self._configure_git()

            return True

        logger.warning("Git is not installed")

        if not click.confirm("Do you want to install Git now?"):
            logger.error("Git is required to clone repositories")
            return False

        if not self.git_installer.install():
            logger.error("Failed to install Git")
            return False

        logger.success("Git installed successfully")

        # Configure Git after installation
        self._configure_git()

        return True

    def _configure_git(self) -> None:
        """Configure Git with user information."""
        logger.subsection("Git Configuration")
        logger.info("Git needs to be configured with your information for committing code.")

        if not click.confirm("Do you want to configure Git now?"):
            logger.warning("Git configuration skipped")
            return

        # Get user name
        user_name = click.prompt("Enter your full name", type=str)

        # Get user email
        user_email = click.prompt("Enter your email", type=str)

        # Ask about SSL verification
        ssl_verify = click.confirm(
            "Enable SSL verification? (Select 'n' if you're on a corporate network with custom certificates)",
            default=True
        )

        # Configure Git
        if self.git_installer.configure(user_name=user_name, user_email=user_email, ssl_verify=ssl_verify):
            logger.success("Git configured successfully")
        else:
            logger.warning("Git configuration had issues, but continuing...")

    def process_repository(self, repo_url: str) -> bool:
        """
        Process a single repository with rollback support.

        Args:
            repo_url: Repository URL

        Returns:
            True if successful, False otherwise
        """
        logger.section(f"Processing: {repo_url}")

        repo_path = None
        try:
            # Clone repository
            repo_name = self.repo_manager.get_repo_name(repo_url)
            repo_path = self.base_dir / repo_name

            if repo_path.exists():
                logger.warning(f"Repository already exists at: {repo_path}")
                if not click.confirm("Do you want to overwrite it?"):
                    return False
                if not self.safe_rmtree(str(repo_path)):
                    logger.error("Failed to remove existing repository (directory may be locked)")
                    return False

            # Validate and clone
            try:
                self.repo_manager.validate_repo_url(repo_url)
            except InvalidURLError as e:
                logger.error(str(e))
                return False

            if not self.repo_manager.clone_repository(repo_url, repo_path):
                logger.error("Failed to clone repository")
                return False

            # Detect technology
            logger.progress("Detecting technology...")
            technology = self.detector.detect(repo_path)

            if technology == Technology.UNKNOWN:
                logger.error("Could not detect project technology")
                self._rollback(repo_path)
                return False

            logger.success(f"Detected: {technology.value}")

            # Install and configure
            installer = self._get_installer(technology, repo_path)
            if not installer:
                logger.error(f"No installer available for {technology.value}")
                self._rollback(repo_path)
                return False

            # Check if already installed
            if not installer.is_installed():
                logger.progress(f"Installing {technology.value}...")
                if not installer.install():
                    logger.error("Installation failed")
                    self._rollback(repo_path)
                    return False
                logger.success("Installation completed")
            else:
                logger.success(f"{technology.value} is already installed")

            # Configure project
            logger.progress("Configuring project...")
            if not installer.configure():
                logger.error("Configuration failed")
                self._rollback(repo_path)
                return False

            logger.success("Configuration completed")
            logger.section(f"Project ready at: {repo_path}")

            return True

        except DevStartError as e:
            logger.error(str(e))
            if repo_path:
                self._rollback(repo_path)
            return False
        except KeyboardInterrupt:
            logger.warning("Operation cancelled by user")
            if repo_path and repo_path.exists():
                self._rollback(repo_path)
            return False

    def _get_installer(self, technology: Technology, repo_path: Path):
        """Get appropriate installer for technology."""
        installers = {
            Technology.JAVA_SPRINGBOOT: JavaInstaller,
            Technology.JAVA_MAVEN: JavaInstaller,
            Technology.JAVA_GRADLE: JavaInstaller,
            Technology.PYTHON: PythonInstaller,
            Technology.NODEJS: NodeJSInstaller
        }

        installer_class = installers.get(technology)
        if installer_class:
            return installer_class(repo_path, self.proxy_manager)
        return None


@click.command()
@click.option('--http-proxy', help='HTTP proxy URL (e.g., http://proxy.company.com:8080)')
@click.option('--https-proxy', help='HTTPS proxy URL (e.g., http://proxy.company.com:8080)')
@click.argument('repositories', nargs=-1, required=True)
def main(http_proxy, https_proxy, repositories):
    """
    dev-start - Technology configurator for developers.

    Clones repositories, detects technologies, and configures development environments.

    Example:
        dev-start https://github.com/user/repo1 https://github.com/user/repo2

    With proxy:
        dev-start --http-proxy http://proxy:8080 --https-proxy http://proxy:8080 <repos>
    """
    logger.banner("DEV-START", "Technology Configurator for Developers")

    cli = DevStartCLI()

    # Setup proxy if provided
    try:
        cli.setup_proxy(http_proxy, https_proxy)
    except DevStartError:
        exit(1)

    # Ensure Git is installed
    if not cli.ensure_git_installed():
        logger.error("Cannot proceed without Git. Exiting...")
        exit(1)

    # Process each repository
    successful = 0
    failed = 0

    for repo_url in repositories:
        try:
            if cli.process_repository(repo_url):
                successful += 1
            else:
                failed += 1
        except DevStartError as e:
            logger.error(f"Error processing {repo_url}", details=str(e))
            failed += 1
        except Exception as e:
            logger.error(f"Unexpected error processing {repo_url}", details=str(e))
            failed += 1

    # Summary
    logger.section("Summary")
    logger.result("Successful", str(successful), success=True)
    logger.result("Failed", str(failed), success=(failed == 0))

    if failed > 0:
        exit(1)


if __name__ == '__main__':
    main()
