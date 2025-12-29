"""Technology detector for repository analysis."""
import os
from pathlib import Path
from typing import Optional, List
from enum import Enum


class Technology(Enum):
    """Supported technologies."""
    JAVA_SPRINGBOOT = "java_springboot"
    PYTHON = "python"
    NODEJS = "nodejs"
    UNKNOWN = "unknown"


class TechnologyDetector:
    """Detects technology used in a repository."""

    DETECTION_PATTERNS = {
        Technology.JAVA_SPRINGBOOT: {
            'files': ['pom.xml', 'build.gradle', 'gradlew'],
            'indicators': ['spring-boot', 'springframework']
        },
        Technology.PYTHON: {
            'files': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
            'indicators': []
        },
        Technology.NODEJS: {
            'files': ['package.json', 'package-lock.json', 'yarn.lock'],
            'indicators': []
        }
    }

    def detect(self, repo_path: Path) -> Technology:
        """
        Detect technology from repository files.

        Args:
            repo_path: Path to the cloned repository

        Returns:
            Technology enum value
        """
        if not repo_path.exists():
            return Technology.UNKNOWN

        files_in_repo = self._get_root_files(repo_path)

        # Check for Java/SpringBoot
        if self._matches_technology(repo_path, files_in_repo, Technology.JAVA_SPRINGBOOT):
            return Technology.JAVA_SPRINGBOOT

        # Check for Python
        if self._matches_technology(repo_path, files_in_repo, Technology.PYTHON):
            return Technology.PYTHON

        # Check for Node.js
        if self._matches_technology(repo_path, files_in_repo, Technology.NODEJS):
            return Technology.NODEJS

        return Technology.UNKNOWN

    def _get_root_files(self, repo_path: Path) -> List[str]:
        """Get list of files in repository root."""
        try:
            return [f.name for f in repo_path.iterdir() if f.is_file()]
        except Exception:
            return []

    def _matches_technology(self, repo_path: Path, files: List[str], tech: Technology) -> bool:
        """Check if repository matches a specific technology."""
        pattern = self.DETECTION_PATTERNS.get(tech)
        if not pattern:
            return False

        # Check for presence of key files
        for file in pattern['files']:
            if file in files:
                # If there are indicators, check file content
                if pattern['indicators']:
                    file_path = repo_path / file
                    if self._check_indicators(file_path, pattern['indicators']):
                        return True
                else:
                    return True

        return False

    def _check_indicators(self, file_path: Path, indicators: List[str]) -> bool:
        """Check if file contains specific indicators."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            return any(indicator in content.lower() for indicator in indicators)
        except Exception:
            return False
