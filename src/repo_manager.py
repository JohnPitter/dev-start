"""Repository management and cloning."""
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import git

from .constants import ALLOWED_URL_SCHEMES, ALLOWED_GIT_HOSTS
from .exceptions import InvalidURLError, CloneError
from .logger import get_logger
from .proxy_manager import ProxyManager

logger = get_logger(__name__)


class RepositoryManager:
    """Manages repository cloning and operations."""

    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager

    def validate_repo_url(self, url: str) -> bool:
        """
        Validate that a repository URL is safe and well-formed.

        Args:
            url: Repository URL to validate

        Returns:
            True if valid

        Raises:
            InvalidURLError: If URL is invalid or not allowed
        """
        if not url or not isinstance(url, str):
            raise InvalidURLError(url or '', "URL cannot be empty")

        url = url.strip()

        # Parse the URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise InvalidURLError(url, f"Failed to parse URL: {e}")

        # Check scheme
        scheme = parsed.scheme.lower()
        if scheme not in ALLOWED_URL_SCHEMES:
            raise InvalidURLError(
                url,
                f"URL scheme '{scheme}' not allowed. "
                f"Allowed schemes: {', '.join(ALLOWED_URL_SCHEMES)}"
            )

        # Check for host
        if not parsed.netloc:
            raise InvalidURLError(url, "URL must include a host")

        # Extract hostname (without port)
        hostname = parsed.netloc.split(':')[0].split('@')[-1].lower()

        # Basic hostname validation
        if not hostname or len(hostname) < 3:
            raise InvalidURLError(url, "Invalid hostname")

        # Check for potential injection attempts
        dangerous_patterns = [
            r'[;&|`$]',  # Shell metacharacters
            r'\.\.',  # Directory traversal
            r'%[0-9a-fA-F]{2}',  # URL encoding that might bypass checks
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, url):
                raise InvalidURLError(url, "URL contains potentially dangerous characters")

        # Validate path exists (should end with repo name)
        if not parsed.path or parsed.path == '/':
            raise InvalidURLError(url, "URL must include a repository path")

        logger.debug(f"URL validated: {url}")
        return True

    def clone_repository(self, repo_url: str, destination: Path) -> bool:
        """
        Clone a git repository.

        Args:
            repo_url: URL of the repository
            destination: Local path to clone to

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate URL first
            self.validate_repo_url(repo_url)

            logger.progress(f"Cloning repository: {repo_url}")

            # Configure git proxy if needed
            env = {}
            if self.proxy_manager.http_proxy:
                env['http_proxy'] = self.proxy_manager.http_proxy
            if self.proxy_manager.https_proxy:
                env['https_proxy'] = self.proxy_manager.https_proxy

            # Create parent directory
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Clone repository
            git.Repo.clone_from(
                repo_url,
                destination,
                env=env if env else None
            )

            logger.success(f"Repository cloned to: {destination}")
            return True

        except InvalidURLError:
            # Re-raise validation errors
            raise
        except git.GitCommandError as e:
            logger.error(f"Git clone failed", details=str(e))
            return False
        except git.InvalidGitRepositoryError as e:
            logger.error(f"Invalid git repository", details=str(e))
            return False
        except PermissionError as e:
            logger.error(f"Permission denied", details=str(e))
            return False
        except Exception as e:
            logger.error(f"Error cloning repository", details=str(e))
            return False

    def get_repo_name(self, repo_url: str) -> str:
        """
        Extract repository name from URL.

        Args:
            repo_url: Repository URL

        Returns:
            Repository name (without .git suffix)
        """
        # Remove .git suffix if present
        name = repo_url.rstrip('/').split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]
        return name
