"""Repository management and cloning."""
from pathlib import Path
from typing import Optional
import git
from .proxy_manager import ProxyManager


class RepositoryManager:
    """Manages repository cloning and operations."""

    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager

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
            print(f"Cloning repository: {repo_url}")

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

            print(f"Repository cloned to: {destination}")
            return True

        except Exception as e:
            print(f"Error cloning repository: {e}")
            return False

    def get_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        # Remove .git suffix if present
        name = repo_url.rstrip('/').split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]
        return name
