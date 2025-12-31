"""Base installer class."""
import hashlib
import os
import subprocess
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple, List

import requests

from ..constants import (
    DOWNLOAD_TIMEOUT,
    BUILD_TIMEOUT,
    DOWNLOAD_CHUNK_SIZE,
    DOWNLOAD_CHECKSUMS,
)
from ..exceptions import (
    DownloadError,
    ExtractionError,
    ChecksumVerificationError,
)
from ..logger import get_logger
from ..proxy_manager import ProxyManager
from ..env_manager import EnvironmentManager

logger = get_logger(__name__)


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

    def download_file(self, url: str, destination: Path,
                      expected_checksum: Optional[str] = None) -> bool:
        """
        Download a file with proxy support and optional checksum verification.

        Args:
            url: URL to download from
            destination: Path to save the file
            expected_checksum: Optional SHA256 checksum to verify

        Returns:
            True if successful, False otherwise
        """
        try:
            proxies = self.proxy_manager.get_proxy_dict()

            logger.progress(f"Downloading from {url}...")
            response = requests.get(
                url,
                proxies=proxies,
                stream=True,
                timeout=DOWNLOAD_TIMEOUT
            )
            response.raise_for_status()

            destination.parent.mkdir(parents=True, exist_ok=True)

            # Calculate file size for progress reporting
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            # Hash for checksum verification
            sha256_hash = hashlib.sha256()

            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    f.write(chunk)
                    sha256_hash.update(chunk)
                    downloaded += len(chunk)

                    # Progress reporting for large files
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        if downloaded % (DOWNLOAD_CHUNK_SIZE * 100) == 0:  # Every 800KB
                            logger.debug(f"Download progress: {percent:.1f}%")

            # Verify checksum if provided
            if expected_checksum:
                actual_checksum = sha256_hash.hexdigest()
                if actual_checksum.lower() != expected_checksum.lower():
                    destination.unlink(missing_ok=True)
                    logger.error(
                        f"Checksum verification failed",
                        details=f"Expected: {expected_checksum}\nActual: {actual_checksum}"
                    )
                    return False
                logger.debug(f"Checksum verified: {actual_checksum[:16]}...")

            logger.success(f"Downloaded successfully: {destination.name}")
            return True

        except requests.exceptions.Timeout:
            logger.error(f"Download timed out after {DOWNLOAD_TIMEOUT}s", details=url)
            return False
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during download: {e.response.status_code}", details=url)
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during download", details=str(e))
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading file", details=str(e))
            return False
        except IOError as e:
            logger.error(f"Error saving file to {destination}", details=str(e))
            return False

    def download_and_extract(self, url: str, extract_dir: Path,
                             expected_checksum: Optional[str] = None,
                             cleanup_zip: bool = True) -> Tuple[bool, Optional[Path]]:
        """
        Download and extract a ZIP file.

        Args:
            url: URL to download from
            extract_dir: Directory to extract to
            expected_checksum: Optional SHA256 checksum to verify
            cleanup_zip: Whether to delete the ZIP file after extraction

        Returns:
            Tuple of (success, extracted_directory_path)
        """
        zip_filename = url.split('/')[-1]
        zip_path = extract_dir / zip_filename

        # Download
        if not self.download_file(url, zip_path, expected_checksum):
            return False, None

        # Extract
        try:
            logger.progress(f"Extracting {zip_filename}...")

            extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get the root directory in the archive (if any)
                namelist = zip_ref.namelist()
                root_dirs = set()
                for name in namelist:
                    parts = name.split('/')
                    if len(parts) > 1:
                        root_dirs.add(parts[0])

                zip_ref.extractall(extract_dir)

            if cleanup_zip:
                zip_path.unlink()

            # Find the extracted directory
            extracted_path = None
            if len(root_dirs) == 1:
                potential_dir = extract_dir / list(root_dirs)[0]
                if potential_dir.is_dir():
                    extracted_path = potential_dir

            logger.success(f"Extracted successfully")
            return True, extracted_path

        except zipfile.BadZipFile as e:
            logger.error(f"Invalid or corrupted ZIP file", details=str(e))
            zip_path.unlink(missing_ok=True)
            return False, None
        except PermissionError as e:
            logger.error(f"Permission denied during extraction", details=str(e))
            return False, None
        except IOError as e:
            logger.error(f"Error extracting archive", details=str(e))
            return False, None

    def add_to_current_path(self, path: str) -> None:
        """
        Add a path to the current process PATH environment variable.

        Args:
            path: Path to add to PATH
        """
        if 'PATH' in os.environ:
            if path not in os.environ['PATH']:
                os.environ['PATH'] = f"{path}{os.pathsep}{os.environ['PATH']}"
                logger.debug(f"Added to current PATH: {path}")
        else:
            os.environ['PATH'] = path
            logger.debug(f"Set PATH to: {path}")

    def set_current_env(self, name: str, value: str) -> None:
        """
        Set an environment variable for the current process.

        Args:
            name: Environment variable name
            value: Environment variable value
        """
        os.environ[name] = value
        logger.debug(f"Set environment variable: {name}={value}")

    def setup_tool_environment(self, tool_name: str, home_path: str, bin_path: str) -> None:
        """
        Setup environment variables for a tool (both current process and permanent).

        Args:
            tool_name: Name of the tool (e.g., 'JAVA', 'MAVEN')
            home_path: Path to the tool's home directory
            bin_path: Path to the tool's bin directory
        """
        home_var = f"{tool_name.upper()}_HOME"

        # Set for current process
        self.set_current_env(home_var, home_path)
        self.add_to_current_path(bin_path)

        # Set for persistence
        self.env_manager.append_to_env(home_var, home_path)
        self.env_manager.set_system_path(bin_path)

        logger.success(f"{tool_name} environment configured")
        logger.info(f"  {home_var}: {home_path}")
        logger.info(f"  PATH: {bin_path} (added)")

    def run_command(self, command: List[str], cwd: Optional[Path] = None,
                    timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        Run a shell command and return success status and output.

        Args:
            command: Command and arguments as a list
            cwd: Working directory (defaults to project_path)
            timeout: Timeout in seconds (defaults to BUILD_TIMEOUT)

        Returns:
            Tuple of (success, output)
        """
        if timeout is None:
            timeout = BUILD_TIMEOUT

        try:
            env = os.environ.copy()
            if self.proxy_manager.http_proxy:
                env['HTTP_PROXY'] = self.proxy_manager.http_proxy
            if self.proxy_manager.https_proxy:
                env['HTTPS_PROXY'] = self.proxy_manager.https_proxy

            logger.debug(f"Running command: {' '.join(command)}")

            result = subprocess.run(
                command,
                cwd=cwd or self.project_path,
                capture_output=True,
                text=True,
                env=env,
                timeout=timeout
            )

            output = result.stdout + result.stderr
            success = result.returncode == 0

            if not success:
                logger.debug(f"Command failed with code {result.returncode}")

            return success, output

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s")
            return False, f"Command timed out after {timeout} seconds"
        except FileNotFoundError as e:
            logger.error(f"Command not found: {command[0]}")
            return False, str(e)
        except PermissionError as e:
            logger.error(f"Permission denied running command")
            return False, str(e)
        except subprocess.SubprocessError as e:
            logger.error(f"Error running command")
            return False, str(e)

    def find_executable(self, name: str, search_paths: Optional[List[Path]] = None) -> Optional[str]:
        """
        Find an executable in PATH or specified paths.

        Args:
            name: Name of the executable (without extension on Windows)
            search_paths: Additional paths to search

        Returns:
            Full path to executable, or None if not found
        """
        import shutil

        # Try additional search paths first (for just-installed tools)
        if search_paths:
            for search_path in search_paths:
                # Try Windows extensions
                for ext in ['', '.cmd', '.bat', '.exe']:
                    candidate = search_path / f"{name}{ext}"
                    if candidate.exists():
                        logger.debug(f"Found {name} at: {candidate}")
                        return str(candidate)

        # Try PATH
        found = shutil.which(name)
        if found:
            logger.debug(f"Found {name} in PATH: {found}")
            return found

        return None
