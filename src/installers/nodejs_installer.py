"""Node.js installer."""
import json
import subprocess
from pathlib import Path
from typing import Optional

from .base import BaseInstaller
from ..constants import (
    DOWNLOAD_URLS,
    DOWNLOAD_CHECKSUMS,
    DEFAULT_VERSIONS,
    BUILD_TIMEOUT,
    get_tools_dir,
)
from ..logger import get_logger

logger = get_logger(__name__)


class NodeJSInstaller(BaseInstaller):
    """Installer for Node.js projects."""

    def detect_version(self) -> Optional[str]:
        """Detect Node.js version from package.json."""
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text(encoding='utf-8'))
                engines = data.get('engines', {})
                node_version = engines.get('node', '')
                if node_version:
                    # Strip version prefixes like ^, ~, >=, etc.
                    return node_version.strip('^~>=<')
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse package.json", details=str(e))
            except IOError as e:
                logger.warning(f"Failed to read package.json", details=str(e))

        return DEFAULT_VERSIONS['nodejs']

    def is_installed(self) -> bool:
        """Check if Node.js is installed."""
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def is_npm_installed(self) -> bool:
        """Check if npm is installed."""
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def install(self) -> bool:
        """Install Node.js."""
        if self.is_installed():
            logger.info("Node.js is already installed")
            return True

        logger.progress("Installing Node.js...")
        tools_dir = get_tools_dir()
        nodejs_dir = tools_dir / 'nodejs'
        version = DEFAULT_VERSIONS['nodejs']

        if not nodejs_dir.exists():
            logger.progress(f"Downloading Node.js {version}...")

            download_url = DOWNLOAD_URLS['nodejs'].get(version)
            expected_checksum = DOWNLOAD_CHECKSUMS.get('nodejs', {}).get(version)

            if not download_url:
                logger.error(f"No download URL for Node.js version {version}")
                return False

            success, extracted_dir = self.download_and_extract(
                download_url,
                tools_dir,
                expected_checksum=expected_checksum
            )

            if not success:
                logger.error("Failed to download Node.js. Please install manually.")
                return False

            # Rename extracted directory
            if extracted_dir and extracted_dir != nodejs_dir and extracted_dir.exists():
                try:
                    extracted_dir.rename(nodejs_dir)
                    logger.debug(f"Renamed {extracted_dir.name} to nodejs")
                except OSError as e:
                    logger.warning(f"Could not rename extracted directory", details=str(e))

        # Setup Node.js environment
        nodejs_path = str(nodejs_dir)
        self.setup_tool_environment('NODE', nodejs_path, nodejs_path)

        logger.success("Node.js installed successfully!")
        return True

    def configure(self) -> bool:
        """Configure Node.js project."""
        logger.progress("Configuring Node.js project...")

        # Check if npm is installed
        if not self.is_npm_installed():
            logger.error("npm not found. npm should be installed with Node.js")
            return False

        logger.success("npm is already installed")

        # Ensure npm configuration exists
        self._ensure_npm_config()

        # Configure npm proxy if needed
        if self.proxy_manager.http_proxy:
            self._configure_npm_proxy()

        # Install dependencies
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            logger.progress("Installing project dependencies with npm...")
            if not self._run_npm_install():
                logger.warning("npm install failed, but continuing...")
                return True  # Don't fail the whole process

        # Create .env file template if doesn't exist
        env_file = self.project_path / '.env'
        if not env_file.exists():
            self.env_manager.create_env_file({
                'NODE_ENV': 'development',
                'PORT': '3000'
            })

        return True

    def _run_npm_install(self) -> bool:
        """Run npm install to download dependencies."""
        logger.progress("Running: npm install")

        success, output = self.run_command(
            ['npm', 'install'],
            timeout=BUILD_TIMEOUT
        )

        if success:
            logger.success("npm dependencies installed successfully")
        else:
            logger.error("npm install failed")
            if output:
                logger.debug(f"Output: {output[:500]}")

        return success

    def _ensure_npm_config(self) -> None:
        """Ensure npm configuration file exists."""
        npmrc_file = Path.home() / '.npmrc'

        if not npmrc_file.exists():
            default_config = """# npm configuration file
registry=https://registry.npmjs.org/
# cache configuration
cache=${HOME}/.npm
# timeout in milliseconds
timeout=60000
"""
            try:
                npmrc_file.write_text(default_config, encoding='utf-8')
                logger.success(f"Created .npmrc: {npmrc_file}")
            except IOError as e:
                logger.warning(f"Could not create .npmrc", details=str(e))
        else:
            logger.info(f".npmrc already exists: {npmrc_file}")

    def _configure_npm_proxy(self) -> None:
        """Configure npm proxy settings."""
        if self.proxy_manager.http_proxy:
            try:
                subprocess.run(
                    ['npm', 'config', 'set', 'proxy', self.proxy_manager.http_proxy],
                    check=True,
                    capture_output=True
                )
                logger.success("npm http proxy configured")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to configure npm proxy", details=str(e))
            except FileNotFoundError:
                logger.warning("npm command not found")

        if self.proxy_manager.https_proxy:
            try:
                subprocess.run(
                    ['npm', 'config', 'set', 'https-proxy', self.proxy_manager.https_proxy],
                    check=True,
                    capture_output=True
                )
                logger.success("npm https proxy configured")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to configure npm https proxy", details=str(e))
