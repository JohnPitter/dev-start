"""Node.js installer."""
import json
import subprocess
import zipfile
from pathlib import Path
from typing import Optional
from .base import BaseInstaller


class NodeJSInstaller(BaseInstaller):
    """Installer for Node.js projects."""

    NODEJS_DOWNLOAD_URL = 'https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip'

    def detect_version(self) -> Optional[str]:
        """Detect Node.js version from package.json."""
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text(encoding='utf-8'))
                engines = data.get('engines', {})
                node_version = engines.get('node', '')
                if node_version:
                    return node_version.strip('^~>=<')
            except Exception:
                pass

        return '20.11.0'  # Default LTS version

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
            print("Node.js is already installed.")
            return True

        print("Installing Node.js...")
        tools_dir = Path.home() / '.dev-start' / 'tools'
        nodejs_dir = tools_dir / 'nodejs'

        if not nodejs_dir.exists():
            print("Downloading Node.js...")
            zip_path = tools_dir / 'nodejs.zip'

            if not self.download_file(self.NODEJS_DOWNLOAD_URL, zip_path):
                print("Failed to download Node.js. Please install manually.")
                return False

            print("Extracting Node.js...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tools_dir)

            # Rename extracted directory
            for item in tools_dir.iterdir():
                if item.is_dir() and item.name.startswith('node-v'):
                    item.rename(nodejs_dir)
                    break

            zip_path.unlink()

        # Add to PATH
        nodejs_path = str(nodejs_dir)

        # Set environment variables for persistence
        self.env_manager.set_system_path(nodejs_path)
        self.env_manager.append_to_env('NODE_HOME', nodejs_path)

        # Update current process environment
        import os
        os.environ['NODE_HOME'] = nodejs_path
        if 'PATH' in os.environ:
            if nodejs_path not in os.environ['PATH']:
                os.environ['PATH'] = f"{nodejs_path}{os.pathsep}{os.environ['PATH']}"
        else:
            os.environ['PATH'] = nodejs_path

        print("✓ Node.js environment variables configured")
        print(f"  NODE_HOME: {nodejs_path}")
        print(f"  PATH: {nodejs_path} (added)")

        return True

    def configure(self) -> bool:
        """Configure Node.js project."""
        print("\nConfiguring Node.js project...")

        # Check if npm is installed
        if not self.is_npm_installed():
            print("\n✗ npm not found. npm should be installed with Node.js")
            return False
        else:
            print("\n✓ npm is already installed")

        # Ensure npm configuration exists
        self._ensure_npm_config()

        # Configure npm proxy if needed
        if self.proxy_manager.http_proxy:
            self._configure_npm_proxy()

        # Install dependencies
        package_json = self.project_path / 'package.json'
        if package_json.exists():
            print("\nInstalling project dependencies with npm...")
            if not self._run_npm_install():
                print("\n⚠ Warning: npm install failed, but continuing...")
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
        try:
            print("\nRunning: npm install")
            result = subprocess.run(
                ['npm', 'install'],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            if result.returncode == 0:
                print("\n✓ npm dependencies installed successfully")
                return True
            else:
                print(f"\n✗ npm install failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr[:500]}")  # Print first 500 chars
                return False
        except subprocess.TimeoutExpired:
            print("\n✗ npm install timed out after 10 minutes")
            return False
        except FileNotFoundError:
            print("\n✗ npm not found in PATH")
            return False
        except Exception as e:
            print(f"\n✗ Error running npm: {e}")
            return False

    def _ensure_npm_config(self):
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
            with open(npmrc_file, 'w', encoding='utf-8') as f:
                f.write(default_config)
            print(f"✓ Created .npmrc: {npmrc_file}")
        else:
            print(f"✓ .npmrc already exists: {npmrc_file}")

    def _configure_npm_proxy(self):
        """Configure npm proxy settings."""
        if self.proxy_manager.http_proxy:
            subprocess.run(['npm', 'config', 'set', 'proxy', self.proxy_manager.http_proxy])
            print(f"✓ npm http proxy configured")

        if self.proxy_manager.https_proxy:
            subprocess.run(['npm', 'config', 'set', 'https-proxy', self.proxy_manager.https_proxy])
            print(f"✓ npm https proxy configured")
