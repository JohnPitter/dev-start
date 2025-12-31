"""Custom exception hierarchy for dev-start."""
from typing import Optional


class DevStartError(Exception):
    """Base exception for all dev-start errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


# =============================================================================
# VALIDATION ERRORS
# =============================================================================
class ValidationError(DevStartError):
    """Base class for validation errors."""
    pass


class InvalidURLError(ValidationError):
    """Raised when a URL is invalid or not allowed."""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(
            f"Invalid URL: {url}",
            details=reason
        )


class InvalidProxyURLError(ValidationError):
    """Raised when a proxy URL is invalid."""

    def __init__(self, url: str):
        self.url = url
        super().__init__(
            f"Invalid proxy URL: {url}",
            details="Proxy URL must be in format: http://host:port or https://host:port"
        )


class InvalidEnvironmentVariableError(ValidationError):
    """Raised when an environment variable name is invalid."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"Invalid environment variable name: {name}",
            details="Environment variable names must start with a letter or underscore, "
                   "and contain only letters, numbers, and underscores"
        )


# =============================================================================
# INSTALLATION ERRORS
# =============================================================================
class InstallationError(DevStartError):
    """Base class for installation-related errors."""
    pass


class DownloadError(InstallationError):
    """Raised when a download fails."""

    def __init__(self, url: str, reason: Optional[str] = None):
        self.url = url
        super().__init__(
            f"Failed to download: {url}",
            details=reason
        )


class ChecksumVerificationError(InstallationError):
    """Raised when checksum verification fails."""

    def __init__(self, file_path: str, expected: str, actual: str):
        self.file_path = file_path
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Checksum verification failed for: {file_path}",
            details=f"Expected: {expected}\nActual: {actual}"
        )


class ExtractionError(InstallationError):
    """Raised when archive extraction fails."""

    def __init__(self, archive_path: str, reason: Optional[str] = None):
        self.archive_path = archive_path
        super().__init__(
            f"Failed to extract archive: {archive_path}",
            details=reason
        )


class ToolNotFoundError(InstallationError):
    """Raised when a required tool is not found."""

    def __init__(self, tool_name: str, install_url: Optional[str] = None):
        self.tool_name = tool_name
        self.install_url = install_url
        details = None
        if install_url:
            details = f"Please install manually from: {install_url}"
        super().__init__(
            f"Required tool not found: {tool_name}",
            details=details
        )


class ConfigurationError(InstallationError):
    """Raised when configuration fails."""

    def __init__(self, component: str, reason: Optional[str] = None):
        self.component = component
        super().__init__(
            f"Failed to configure: {component}",
            details=reason
        )


# =============================================================================
# DETECTION ERRORS
# =============================================================================
class DetectionError(DevStartError):
    """Base class for technology detection errors."""
    pass


class UnknownTechnologyError(DetectionError):
    """Raised when technology cannot be detected."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        super().__init__(
            f"Could not detect technology in repository: {repo_path}",
            details="No recognizable project files found (pom.xml, package.json, requirements.txt, etc.)"
        )


# =============================================================================
# REPOSITORY ERRORS
# =============================================================================
class RepositoryError(DevStartError):
    """Base class for repository-related errors."""
    pass


class CloneError(RepositoryError):
    """Raised when repository cloning fails."""

    def __init__(self, url: str, reason: Optional[str] = None):
        self.url = url
        super().__init__(
            f"Failed to clone repository: {url}",
            details=reason
        )


class RepositoryExistsError(RepositoryError):
    """Raised when repository already exists and overwrite is not confirmed."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(
            f"Repository already exists at: {path}",
            details="Use --force to overwrite or manually delete the directory"
        )


# =============================================================================
# ENVIRONMENT ERRORS
# =============================================================================
class EnvironmentError(DevStartError):
    """Base class for environment-related errors."""
    pass


class PathUpdateError(EnvironmentError):
    """Raised when PATH update fails."""

    def __init__(self, path: str, reason: Optional[str] = None):
        self.path = path
        super().__init__(
            f"Failed to add path to system PATH: {path}",
            details=reason
        )


class EnvironmentVariableError(EnvironmentError):
    """Raised when setting environment variable fails."""

    def __init__(self, name: str, reason: Optional[str] = None):
        self.name = name
        super().__init__(
            f"Failed to set environment variable: {name}",
            details=reason
        )


# =============================================================================
# BUILD ERRORS
# =============================================================================
class BuildError(DevStartError):
    """Base class for build-related errors."""
    pass


class MavenBuildError(BuildError):
    """Raised when Maven build fails."""

    def __init__(self, project_path: str, reason: Optional[str] = None):
        self.project_path = project_path
        super().__init__(
            f"Maven build failed in: {project_path}",
            details=reason
        )


class GradleBuildError(BuildError):
    """Raised when Gradle build fails."""

    def __init__(self, project_path: str, reason: Optional[str] = None):
        self.project_path = project_path
        super().__init__(
            f"Gradle build failed in: {project_path}",
            details=reason
        )


class NpmInstallError(BuildError):
    """Raised when npm install fails."""

    def __init__(self, project_path: str, reason: Optional[str] = None):
        self.project_path = project_path
        super().__init__(
            f"npm install failed in: {project_path}",
            details=reason
        )


class PipInstallError(BuildError):
    """Raised when pip install fails."""

    def __init__(self, project_path: str, reason: Optional[str] = None):
        self.project_path = project_path
        super().__init__(
            f"pip install failed in: {project_path}",
            details=reason
        )


# =============================================================================
# TIMEOUT ERRORS
# =============================================================================
class TimeoutError(DevStartError):
    """Raised when an operation times out."""

    def __init__(self, operation: str, timeout_seconds: int):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Operation timed out: {operation}",
            details=f"Timeout after {timeout_seconds} seconds"
        )


# =============================================================================
# ROLLBACK ERRORS
# =============================================================================
class RollbackError(DevStartError):
    """Raised when rollback operation fails."""

    def __init__(self, reason: Optional[str] = None):
        super().__init__(
            "Failed to rollback partial installation",
            details=reason
        )
