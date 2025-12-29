"""Command-line interface for dev-start."""
import click
import os
import stat
import time
import shutil
from pathlib import Path
from colorama import init, Fore, Style
from .proxy_manager import ProxyManager
from .repo_manager import RepositoryManager
from .detector import TechnologyDetector, Technology
from .installers.git_installer import GitInstaller
from .installers.java_installer import JavaInstaller
from .installers.python_installer import PythonInstaller
from .installers.nodejs_installer import NodeJSInstaller

# Initialize colorama for Windows
init(autoreset=True)


class DevStartCLI:
    """Main CLI application."""

    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.repo_manager = RepositoryManager(self.proxy_manager)
        self.detector = TechnologyDetector()
        self.base_dir = Path.home() / 'dev-start-projects'
        self.base_dir.mkdir(exist_ok=True)
        self.git_installer = None

    def setup_proxy(self, http_proxy: str = None, https_proxy: str = None):
        """Configure proxy settings."""
        if http_proxy or https_proxy:
            print(f"{Fore.CYAN}Configuring proxy settings...")
            self.proxy_manager.set_proxy(http_proxy, https_proxy)
            print(f"{Fore.GREEN}✓ Proxy configured")

    def remove_readonly(self, func, path, excinfo):
        """Error handler for shutil.rmtree to handle read-only files."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def safe_rmtree(self, path, max_retries=3):
        """Safely remove directory tree with retry logic for locked files."""
        for attempt in range(max_retries):
            try:
                if os.path.exists(path):
                    # First attempt: standard removal with error handler
                    shutil.rmtree(path, onerror=self.remove_readonly)
                    print(f"{Fore.GREEN}✓ Removed existing directory")
                    return True
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"{Fore.YELLOW}⚠ Attempt {attempt + 1}/{max_retries}: Directory is locked, retrying in 1s...")
                    time.sleep(1)
                else:
                    print(f"{Fore.RED}✗ Failed to remove directory after {max_retries} attempts")
                    print(f"{Fore.RED}  Error: {e}")
                    print(f"{Fore.YELLOW}  Please close any programs using files in: {path}")
                    print(f"{Fore.YELLOW}  Then manually delete the directory and try again")
                    return False
            except Exception as e:
                print(f"{Fore.RED}✗ Error removing directory: {e}")
                return False
        return False

    def ensure_git_installed(self) -> bool:
        """Ensure Git is installed before processing repositories."""
        print(f"\n{Fore.CYAN}Checking Git installation...")

        # Create Git installer instance
        self.git_installer = GitInstaller(self.base_dir, self.proxy_manager)

        if self.git_installer.is_installed():
            version = self.git_installer.detect_version()
            print(f"{Fore.GREEN}✓ Git is installed (version {version})")

            # Check if Git needs configuration
            if not self.git_installer._is_git_configured():
                print(f"{Fore.YELLOW}⚠ Git is not configured")
                self._configure_git()

            return True

        print(f"{Fore.YELLOW}⚠ Git is not installed")

        if not click.confirm("Do you want to install Git now?"):
            print(f"{Fore.RED}✗ Git is required to clone repositories")
            return False

        if not self.git_installer.install():
            print(f"{Fore.RED}✗ Failed to install Git")
            return False

        print(f"{Fore.GREEN}✓ Git installed successfully")

        # Configure Git after installation
        self._configure_git()

        return True

    def _configure_git(self):
        """Configure Git with user information."""
        print(f"\n{Fore.CYAN}⚙ Git Configuration")
        print("Git needs to be configured with your information for committing code.")

        if not click.confirm("Do you want to configure Git now?"):
            print(f"{Fore.YELLOW}⚠ Git configuration skipped")
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
            print(f"{Fore.GREEN}✓ Git configured successfully")
        else:
            print(f"{Fore.YELLOW}⚠ Git configuration had issues, but continuing...")

    def process_repository(self, repo_url: str) -> bool:
        """
        Process a single repository.

        Args:
            repo_url: Repository URL

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}Processing: {repo_url}")
        print(f"{Fore.CYAN}{'='*60}\n")

        # Clone repository
        repo_name = self.repo_manager.get_repo_name(repo_url)
        repo_path = self.base_dir / repo_name

        if repo_path.exists():
            print(f"{Fore.YELLOW}⚠ Repository already exists at: {repo_path}")
            if not click.confirm("Do you want to overwrite it?"):
                return False
            if not self.safe_rmtree(str(repo_path)):
                print(f"{Fore.RED}✗ Failed to remove existing repository (directory may be locked)")
                return False

        if not self.repo_manager.clone_repository(repo_url, repo_path):
            print(f"{Fore.RED}✗ Failed to clone repository")
            return False

        # Detect technology
        print(f"\n{Fore.CYAN}Detecting technology...")
        technology = self.detector.detect(repo_path)

        if technology == Technology.UNKNOWN:
            print(f"{Fore.RED}✗ Could not detect project technology")
            return False

        print(f"{Fore.GREEN}✓ Detected: {technology.value}")

        # Install and configure
        installer = self._get_installer(technology, repo_path)
        if not installer:
            print(f"{Fore.RED}✗ No installer available for {technology.value}")
            return False

        # Check if already installed
        if not installer.is_installed():
            print(f"\n{Fore.CYAN}Installing {technology.value}...")
            if not installer.install():
                print(f"{Fore.RED}✗ Installation failed")
                return False
            print(f"{Fore.GREEN}✓ Installation completed")
        else:
            print(f"{Fore.GREEN}✓ {technology.value} is already installed")

        # Configure project
        print(f"\n{Fore.CYAN}Configuring project...")
        if not installer.configure():
            print(f"{Fore.RED}✗ Configuration failed")
            return False

        print(f"{Fore.GREEN}✓ Configuration completed")
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"{Fore.GREEN}✓ Project ready at: {repo_path}")
        print(f"{Fore.GREEN}{'='*60}\n")

        return True

    def _get_installer(self, technology: Technology, repo_path: Path):
        """Get appropriate installer for technology."""
        installers = {
            Technology.JAVA_SPRINGBOOT: JavaInstaller,
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
    print(f"{Fore.CYAN}{Style.BRIGHT}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                      DEV-START                             ║")
    print("║           Technology Configurator for Developers           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(Style.RESET_ALL)

    cli = DevStartCLI()

    # Setup proxy if provided
    cli.setup_proxy(http_proxy, https_proxy)

    # Ensure Git is installed
    if not cli.ensure_git_installed():
        print(f"\n{Fore.RED}Cannot proceed without Git. Exiting...")
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
        except Exception as e:
            print(f"{Fore.RED}✗ Error processing {repo_url}: {e}")
            failed += 1

    # Summary
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}Successful: {successful}")
    print(f"{Fore.RED}Failed: {failed}")
    print(f"{Fore.CYAN}{'='*60}\n")

    if failed > 0:
        exit(1)


if __name__ == '__main__':
    main()
