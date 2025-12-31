"""Centralized constants and configuration values for dev-start."""
from pathlib import Path
from typing import Dict

# =============================================================================
# DIRECTORY CONFIGURATION
# =============================================================================
BASE_DIR_NAME = 'dev-start-projects'
TOOLS_DIR_NAME = '.dev-start'
TOOLS_SUBDIR = 'tools'

def get_base_dir() -> Path:
    """Get the base directory for cloned projects."""
    return Path.home() / BASE_DIR_NAME

def get_tools_dir() -> Path:
    """Get the tools installation directory."""
    return Path.home() / TOOLS_DIR_NAME / TOOLS_SUBDIR

# =============================================================================
# TIMEOUT CONFIGURATION (in seconds)
# =============================================================================
DOWNLOAD_TIMEOUT = 300  # 5 minutes for downloads
BUILD_TIMEOUT = 600  # 10 minutes for builds (Maven, Gradle, npm)
COMMAND_TIMEOUT = 120  # 2 minutes for general commands
GIT_TIMEOUT = 10  # 10 seconds for git version checks

# =============================================================================
# DEFAULT VERSIONS
# =============================================================================
DEFAULT_VERSIONS: Dict[str, str] = {
    'java': '17',
    'python': '3.11',
    'nodejs': '20.11.0',
    'git': '2.43.0',
    'maven': '3.9.9',
}

# =============================================================================
# DOWNLOAD URLS
# =============================================================================
DOWNLOAD_URLS: Dict[str, Dict[str, str]] = {
    'git': {
        '2.43.0': 'https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/MinGit-2.43.0-64-bit.zip'
    },
    'java': {
        '17': 'https://download.oracle.com/java/17/latest/jdk-17_windows-x64_bin.zip',
        '11': 'https://download.oracle.com/java/11/latest/jdk-11_windows-x64_bin.zip'
    },
    'maven': {
        '3.9.9': [
            'https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.zip',
            'https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.zip',
            'https://mirrors.estointernet.in/apache/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.zip'
        ]
    },
    'nodejs': {
        '20.11.0': 'https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip'
    },
    'python': {
        '3.11': 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe'
    }
}

# =============================================================================
# SHA256 CHECKSUMS FOR DOWNLOAD VERIFICATION
# =============================================================================
DOWNLOAD_CHECKSUMS: Dict[str, Dict[str, str]] = {
    'git': {
        '2.43.0': 'e94ef7ecce4aea9a075f5e1cd80371abaf69db5e713e78fa5aa7fd8fc56a14a5'
    },
    'nodejs': {
        '20.11.0': '4226e02e78f7fd54294f31b2a945f5e04e9e0ffa399a6fb16ccbe9d4cfcf5f80'
    },
    # Note: Oracle Java and Maven don't provide stable checksums for "latest" URLs
    # Checksums should be updated when version-specific URLs are used
}

# =============================================================================
# URL VALIDATION
# =============================================================================
ALLOWED_URL_SCHEMES = ['http', 'https', 'git']
ALLOWED_GIT_HOSTS = [
    'github.com',
    'gitlab.com',
    'bitbucket.org',
    'dev.azure.com',
    'ssh.dev.azure.com',
]

# =============================================================================
# ENVIRONMENT VARIABLE PATTERNS
# =============================================================================
ENV_VAR_NAME_PATTERN = r'^[A-Za-z_][A-Za-z0-9_]*$'

# =============================================================================
# PROXY URL PATTERN
# =============================================================================
PROXY_URL_PATTERN = r'^https?://[^\s/$.?#].[^\s]*$'

# =============================================================================
# RETRY CONFIGURATION
# =============================================================================
MAX_DOWNLOAD_RETRIES = 3
MAX_RMTREE_RETRIES = 3
RETRY_DELAY_SECONDS = 1

# =============================================================================
# CHUNK SIZE FOR DOWNLOADS
# =============================================================================
DOWNLOAD_CHUNK_SIZE = 8192  # 8 KB

# =============================================================================
# GUI CONFIGURATION
# =============================================================================
GUI_WINDOW_WIDTH = 1000
GUI_WINDOW_HEIGHT = 750
GUI_MIN_WIDTH = 800
GUI_MIN_HEIGHT = 600

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FILE_NAME = 'dev-start.log'
