"""Base installer class."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import os
import subprocess
import requests
from ..proxy_manager import ProxyManager
from ..env_manager import EnvironmentManager


class BaseInstaller(ABC):
    """Abstract base class for technology installers."""

    def __init__(self, project_path: Path, proxy_manager: ProxyManager):
        self.project_path = project_path
        self.proxy_manager = proxy_manager
        self.env_manager = EnvironmentManager(project_path)

    @abstractmethod
    def detect_version(self) -> Optional[str]:
        """Detect required version from project files."""
        pass

    @abstractmethod
    def is_installed(self) -> bool:
        """Check if technology is already installed."""
        pass

    @abstractmethod
    def install(self) -> bool:
        """Install the technology."""
        pass

    @abstractmethod
    def configure(self) -> bool:
        """Configure the project."""
        pass

    def download_file(self, url: str, destination: Path) -> bool:
        """Download a file with proxy support."""
        try:
            proxies = self.proxy_manager.get_proxy_dict()
            response = requests.get(url, proxies=proxies, stream=True, timeout=300)
            response.raise_for_status()

            destination.parent.mkdir(parents=True, exist_ok=True)
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False

    def run_command(self, command: list, cwd: Optional[Path] = None) -> tuple[bool, str]:
        """Run a shell command and return success status and output."""
        try:
            env = os.environ.copy()
            if self.proxy_manager.http_proxy:
                env['HTTP_PROXY'] = self.proxy_manager.http_proxy
            if self.proxy_manager.https_proxy:
                env['HTTPS_PROXY'] = self.proxy_manager.https_proxy

            result = subprocess.run(
                command,
                cwd=cwd or self.project_path,
                capture_output=True,
                text=True,
                env=env,
                timeout=600
            )
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
