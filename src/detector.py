"""Technology detector for repository analysis."""
from pathlib import Path
from typing import Optional, List, Set
from enum import Enum

from .logger import get_logger
from .exceptions import DetectionError

logger = get_logger(__name__)


class Technology(Enum):
    """Supported technologies."""
    JAVA_SPRINGBOOT = "java_springboot"
    JAVA_MAVEN = "java_maven"
    JAVA_GRADLE = "java_gradle"
    PYTHON = "python"
    NODEJS = "nodejs"
    UNKNOWN = "unknown"


class BuildTool(Enum):
    """Build tools for Java projects."""
    MAVEN = "maven"
    GRADLE = "gradle"
    UNKNOWN = "unknown"


class TechnologyDetector:
    """Detects technology used in a repository."""

    # Detection patterns for each technology
    DETECTION_PATTERNS = {
        Technology.JAVA_SPRINGBOOT: {
            'files': ['pom.xml', 'build.gradle', 'build.gradle.kts', 'gradlew'],
            'indicators': ['spring-boot', 'springframework', 'org.springframework']
        },
        Technology.JAVA_MAVEN: {
            'files': ['pom.xml'],
            'indicators': []  # Any Maven project without Spring
        },
        Technology.JAVA_GRADLE: {
            'files': ['build.gradle', 'build.gradle.kts', 'gradlew', 'gradlew.bat'],
            'indicators': []  # Any Gradle project without Spring
        },
        Technology.PYTHON: {
            'files': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile', 'setup.cfg'],
            'indicators': []
        },
        Technology.NODEJS: {
            'files': ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'],
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
            logger.warning(f"Repository path does not exist: {repo_path}")
            return Technology.UNKNOWN

        files_in_repo = self._get_root_files(repo_path)
        logger.debug(f"Files in repository root: {files_in_repo}")

        # Check for Java/SpringBoot (highest priority for Spring projects)
        if self._is_spring_boot_project(repo_path, files_in_repo):
            logger.info(f"Detected: Spring Boot project")
            return Technology.JAVA_SPRINGBOOT

        # Check for Java Maven (non-Spring)
        if self._is_maven_project(repo_path, files_in_repo):
            logger.info(f"Detected: Java Maven project")
            return Technology.JAVA_SPRINGBOOT  # Use same installer

        # Check for Java Gradle (non-Spring)
        if self._is_gradle_project(repo_path, files_in_repo):
            logger.info(f"Detected: Java Gradle project")
            return Technology.JAVA_SPRINGBOOT  # Use same installer

        # Check for Python
        if self._matches_technology(repo_path, files_in_repo, Technology.PYTHON):
            logger.info(f"Detected: Python project")
            return Technology.PYTHON

        # Check for Node.js
        if self._matches_technology(repo_path, files_in_repo, Technology.NODEJS):
            logger.info(f"Detected: Node.js project")
            return Technology.NODEJS

        logger.warning(f"Could not detect technology in: {repo_path}")
        return Technology.UNKNOWN

    def detect_build_tool(self, repo_path: Path) -> BuildTool:
        """
        Detect the build tool used in a Java project.

        Args:
            repo_path: Path to the repository

        Returns:
            BuildTool enum value
        """
        files_in_repo = self._get_root_files(repo_path)

        # Check for Gradle first (higher priority if both exist)
        gradle_files = {'build.gradle', 'build.gradle.kts', 'gradlew', 'gradlew.bat', 'settings.gradle', 'settings.gradle.kts'}
        if gradle_files & set(files_in_repo):
            logger.debug("Build tool detected: Gradle")
            return BuildTool.GRADLE

        # Check for Maven
        if 'pom.xml' in files_in_repo:
            logger.debug("Build tool detected: Maven")
            return BuildTool.MAVEN

        return BuildTool.UNKNOWN

    def _get_root_files(self, repo_path: Path) -> List[str]:
        """Get list of files in repository root."""
        try:
            return [f.name for f in repo_path.iterdir() if f.is_file()]
        except PermissionError as e:
            logger.error(f"Permission denied accessing: {repo_path}", details=str(e))
            return []
        except OSError as e:
            logger.error(f"Error reading directory: {repo_path}", details=str(e))
            return []

    def _is_spring_boot_project(self, repo_path: Path, files: List[str]) -> bool:
        """Check if repository is a Spring Boot project."""
        pattern = self.DETECTION_PATTERNS[Technology.JAVA_SPRINGBOOT]

        for file in pattern['files']:
            if file in files:
                file_path = repo_path / file
                if self._check_indicators(file_path, pattern['indicators']):
                    return True

        return False

    def _is_maven_project(self, repo_path: Path, files: List[str]) -> bool:
        """Check if repository is a Maven project (non-Spring)."""
        return 'pom.xml' in files

    def _is_gradle_project(self, repo_path: Path, files: List[str]) -> bool:
        """Check if repository is a Gradle project."""
        gradle_files = {'build.gradle', 'build.gradle.kts', 'settings.gradle', 'settings.gradle.kts'}
        return bool(gradle_files & set(files))

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
            content_lower = content.lower()
            return any(indicator.lower() in content_lower for indicator in indicators)
        except PermissionError as e:
            logger.warning(f"Permission denied reading: {file_path}")
            return False
        except IOError as e:
            logger.warning(f"Error reading file: {file_path}", details=str(e))
            return False
