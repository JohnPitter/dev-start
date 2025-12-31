"""Java/SpringBoot installer."""
import subprocess
from pathlib import Path
from typing import Optional, List
import xml.etree.ElementTree as ET

from .base import BaseInstaller
from ..constants import (
    DOWNLOAD_URLS,
    DEFAULT_VERSIONS,
    BUILD_TIMEOUT,
    get_tools_dir,
)
from ..detector import TechnologyDetector, BuildTool
from ..logger import get_logger
from ..exceptions import ExtractionError

logger = get_logger(__name__)


class JavaInstaller(BaseInstaller):
    """Installer for Java and Maven/Gradle projects."""

    def detect_version(self) -> Optional[str]:
        """Detect Java version from pom.xml or build.gradle."""
        pom_file = self.project_path / 'pom.xml'
        if pom_file.exists():
            return self._detect_from_pom(pom_file)

        gradle_file = self.project_path / 'build.gradle'
        if gradle_file.exists():
            return self._detect_from_gradle(gradle_file)

        gradle_kts_file = self.project_path / 'build.gradle.kts'
        if gradle_kts_file.exists():
            return self._detect_from_gradle(gradle_kts_file)

        return DEFAULT_VERSIONS['java']

    def _detect_from_pom(self, pom_file: Path) -> str:
        """Extract Java version from pom.xml."""
        try:
            tree = ET.parse(pom_file)
            root = tree.getroot()
            ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}

            # Check for java.version property
            for prop in root.findall('.//maven:properties/maven:java.version', ns):
                return prop.text.strip()

            # Check for maven.compiler.source
            for prop in root.findall('.//maven:properties/maven:maven.compiler.source', ns):
                return prop.text.strip()

        except ET.ParseError as e:
            logger.warning(f"Failed to parse pom.xml", details=str(e))
        except IOError as e:
            logger.warning(f"Failed to read pom.xml", details=str(e))

        return DEFAULT_VERSIONS['java']

    def _detect_from_gradle(self, gradle_file: Path) -> str:
        """Extract Java version from build.gradle."""
        try:
            content = gradle_file.read_text(encoding='utf-8')
            if 'sourceCompatibility' in content:
                for line in content.split('\n'):
                    if 'sourceCompatibility' in line and '=' in line:
                        version = line.split('=')[1].strip().strip("'\"")
                        return version
        except IOError as e:
            logger.warning(f"Failed to read gradle file", details=str(e))

        return DEFAULT_VERSIONS['java']

    def is_installed(self) -> bool:
        """Check if Java is installed."""
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def is_maven_installed(self) -> bool:
        """Check if Maven is installed."""
        try:
            result = subprocess.run(['mvn', '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def install(self) -> bool:
        """Install Java and Maven."""
        logger.progress("Installing Java...")
        version = self.detect_version()

        # Use version 17 if specific version not available
        download_version = version if version in DOWNLOAD_URLS['java'] else DEFAULT_VERSIONS['java']

        tools_dir = get_tools_dir()
        java_dir = tools_dir / f'jdk-{download_version}'

        if not java_dir.exists():
            logger.progress(f"Downloading Java {download_version}...")
            download_url = DOWNLOAD_URLS['java'].get(download_version)

            if not download_url:
                logger.error(f"No download URL for Java version {download_version}")
                return False

            success, extracted_dir = self.download_and_extract(download_url, tools_dir)

            if not success:
                logger.error("Failed to download Java. Please install manually.")
                return False

            # Rename extracted directory if needed
            if extracted_dir and extracted_dir != java_dir and extracted_dir.exists():
                try:
                    extracted_dir.rename(java_dir)
                except OSError as e:
                    logger.warning(f"Could not rename extracted directory", details=str(e))

        # Setup Java environment
        java_home = str(java_dir)
        java_bin = str(java_dir / 'bin')
        self.setup_tool_environment('JAVA', java_home, java_bin)

        # Install Maven if pom.xml exists
        if (self.project_path / 'pom.xml').exists():
            return self._install_maven(tools_dir)

        return True

    def _install_maven(self, tools_dir: Path) -> bool:
        """Install Apache Maven with fallback URLs."""
        maven_dir = tools_dir / 'maven'

        if not maven_dir.exists():
            logger.progress("Downloading Maven...")

            maven_urls = DOWNLOAD_URLS['maven'].get(DEFAULT_VERSIONS['maven'], [])
            if isinstance(maven_urls, str):
                maven_urls = [maven_urls]

            # Try each URL until one succeeds
            download_success = False
            for url in maven_urls:
                logger.info(f"Trying: {url}")
                success, extracted_dir = self.download_and_extract(url, tools_dir)

                if success:
                    download_success = True
                    logger.success("Maven downloaded successfully")

                    # Rename extracted directory
                    if extracted_dir and extracted_dir.exists():
                        try:
                            extracted_dir.rename(maven_dir)
                            logger.debug(f"Renamed {extracted_dir.name} to maven")
                        except OSError as e:
                            logger.error(f"Failed to rename Maven directory", details=str(e))
                            return False
                    break
                else:
                    logger.warning("Failed to download from this mirror, trying next...")

            if not download_success:
                logger.error("Failed to download Maven from all mirrors")
                logger.info("Please install Maven manually from: https://maven.apache.org/download.cgi")
                return False

            # Verify Maven bin directory
            maven_bin_dir = maven_dir / 'bin'
            if maven_bin_dir.exists():
                logger.success(f"Maven bin directory found: {maven_bin_dir}")
            else:
                logger.error(f"Maven bin directory not found at: {maven_bin_dir}")
                # List directory contents for debugging
                if maven_dir.exists():
                    contents = [item.name for item in maven_dir.iterdir()]
                    logger.debug(f"Maven directory contents: {contents}")
                return False

        # Setup Maven environment
        maven_home = str(maven_dir)
        maven_bin = str(maven_dir / 'bin')
        self.setup_tool_environment('MAVEN', maven_home, maven_bin)

        return True

    def configure(self) -> bool:
        """Configure Java project."""
        logger.progress("Configuring Java project...")

        # Detect build tool
        detector = TechnologyDetector()
        build_tool = detector.detect_build_tool(self.project_path)

        maven_available = False
        gradle_available = False

        # Handle Maven projects
        if (self.project_path / 'pom.xml').exists():
            if not self.is_maven_installed():
                logger.info("Maven not found. Installing Maven...")
                tools_dir = get_tools_dir()
                tools_dir.mkdir(parents=True, exist_ok=True)
                if self._install_maven(tools_dir):
                    maven_available = True
                    logger.success("Maven installed successfully")
                else:
                    logger.warning("Failed to install Maven")
                    logger.warning("Skipping dependency installation - please install Maven manually")
            else:
                logger.success("Maven is already installed")
                maven_available = True

            if maven_available:
                self._ensure_maven_directories()

        # Create application.properties if needed (for Spring Boot)
        app_props = self.project_path / 'src' / 'main' / 'resources' / 'application.properties'
        if not app_props.exists() and (self.project_path / 'pom.xml').exists():
            self.env_manager.write_config_file(
                'application.properties',
                '# Application configuration\nserver.port=8080\n',
                'src/main/resources'
            )

        # Set proxy for Maven if needed
        if self.proxy_manager.http_proxy and maven_available:
            self._configure_maven_proxy()

        # Run build based on detected build tool
        build_success = False

        if build_tool == BuildTool.GRADLE or (self.project_path / 'build.gradle').exists():
            logger.progress("Installing project dependencies with Gradle...")
            if self._run_gradle_build():
                build_success = True
            else:
                logger.warning("Gradle build failed, but continuing...")
        elif maven_available and (self.project_path / 'pom.xml').exists():
            logger.progress("Installing project dependencies with Maven...")
            if self._run_maven_install():
                build_success = True
            else:
                logger.warning("Maven install failed, but continuing...")

        # Validate build artifacts
        if build_success:
            self._validate_build()

        return True

    def _validate_build(self) -> None:
        """Validate that build artifacts were created successfully."""
        logger.section("Build Validation")

        # Check for Maven build artifacts
        target_dir = self.project_path / 'target'
        if target_dir.exists():
            jar_files = list(target_dir.glob('*.jar'))
            if jar_files:
                logger.success("Build artifacts found:")
                for jar in jar_files:
                    size_mb = jar.stat().st_size / (1024 * 1024)
                    logger.info(f"  - {jar.name} ({size_mb:.2f} MB)")
                logger.success("Application is ready to run!")
                logger.info(f"  To run: cd {self.project_path} && java -jar target/{jar_files[0].name}")
            else:
                logger.warning("No JAR files found in target directory")

        # Check for Gradle build artifacts
        build_dir = self.project_path / 'build'
        if build_dir.exists():
            libs_dir = build_dir / 'libs'
            if libs_dir.exists():
                jar_files = list(libs_dir.glob('*.jar'))
                if jar_files:
                    logger.success("Build artifacts found:")
                    for jar in jar_files:
                        size_mb = jar.stat().st_size / (1024 * 1024)
                        logger.info(f"  - {jar.name} ({size_mb:.2f} MB)")
                    logger.success("Application is ready to run!")
                    logger.info(f"  To run: cd {self.project_path} && java -jar build/libs/{jar_files[0].name}")

    def _run_maven_install(self) -> bool:
        """Run Maven clean install to download dependencies."""
        logger.progress("Searching for Maven executable...")
        maven_cmd = self._find_maven_executable()

        if not maven_cmd:
            tools_dir = get_tools_dir()
            maven_dir = tools_dir / 'maven'
            logger.error("Maven (mvn) not found in PATH or installation directory")
            logger.info(f"Checked locations: {maven_dir / 'bin'}, PATH")
            return False

        logger.progress(f"Running: mvn clean install -DskipTests")
        logger.debug(f"Full path: {maven_cmd}")

        success, output = self.run_command(
            [maven_cmd, 'clean', 'install', '-DskipTests'],
            timeout=BUILD_TIMEOUT
        )

        if success:
            logger.success("Maven dependencies installed successfully")
            logger.success("Project built successfully")
        else:
            logger.error("Maven install failed")
            if output:
                logger.debug(f"Output: {output[:500]}")

        return success

    def _find_maven_executable(self) -> Optional[str]:
        """Find Maven executable in PATH or installation directory."""
        tools_dir = get_tools_dir()
        maven_dir = tools_dir / 'maven'

        return self.find_executable('mvn', [maven_dir / 'bin'])

    def _run_gradle_build(self) -> bool:
        """Run Gradle build to download dependencies."""
        # Try gradlew first (Windows)
        gradlew_bat = self.project_path / 'gradlew.bat'
        gradlew = self.project_path / 'gradlew'

        if gradlew_bat.exists():
            gradle_cmd = str(gradlew_bat)
        elif gradlew.exists():
            gradle_cmd = str(gradlew)
        else:
            # Fall back to system gradle
            gradle_cmd = self.find_executable('gradle')
            if not gradle_cmd:
                logger.error("Gradle not found")
                return False

        logger.progress(f"Running: {Path(gradle_cmd).name} build -x test")

        success, output = self.run_command(
            [gradle_cmd, 'build', '-x', 'test'],
            timeout=BUILD_TIMEOUT
        )

        if success:
            logger.success("Gradle dependencies installed successfully")
        else:
            logger.error("Gradle build failed")
            if output:
                logger.debug(f"Output: {output[:500]}")

        return success

    def _ensure_maven_directories(self) -> None:
        """Ensure Maven directories exist."""
        maven_home = Path.home() / '.m2'
        maven_home.mkdir(exist_ok=True)
        logger.success(f"Maven directory created/verified: {maven_home}")

        # Create repository directory
        repository_dir = maven_home / 'repository'
        repository_dir.mkdir(exist_ok=True)

        # Create default settings.xml if it doesn't exist
        settings_file = maven_home / 'settings.xml'
        if not settings_file.exists():
            default_settings = """<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
          http://maven.apache.org/xsd/settings-1.0.0.xsd">
  <localRepository>${user.home}/.m2/repository</localRepository>
</settings>
"""
            settings_file.write_text(default_settings, encoding='utf-8')
            logger.success(f"Created Maven settings.xml: {settings_file}")

    def _configure_maven_proxy(self) -> None:
        """Configure Maven proxy settings."""
        maven_dir = Path.home() / '.m2'
        maven_dir.mkdir(exist_ok=True)
        settings_file = maven_dir / 'settings.xml'

        proxy_host = self._get_proxy_host(self.proxy_manager.http_proxy)
        proxy_port = self._get_proxy_port(self.proxy_manager.http_proxy)

        proxy_config = f"""<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0
          http://maven.apache.org/xsd/settings-1.0.0.xsd">
  <localRepository>${{user.home}}/.m2/repository</localRepository>
  <proxies>
    <proxy>
      <id>http-proxy</id>
      <active>true</active>
      <protocol>http</protocol>
      <host>{proxy_host}</host>
      <port>{proxy_port}</port>
    </proxy>
  </proxies>
</settings>
"""
        settings_file.write_text(proxy_config, encoding='utf-8')
        logger.success("Maven proxy configured in settings.xml")

    def _get_proxy_host(self, proxy_url: str) -> str:
        """Extract host from proxy URL."""
        if '://' in proxy_url:
            proxy_url = proxy_url.split('://')[1]
        return proxy_url.split(':')[0]

    def _get_proxy_port(self, proxy_url: str) -> str:
        """Extract port from proxy URL."""
        if '://' in proxy_url:
            proxy_url = proxy_url.split('://')[1]
        if ':' in proxy_url:
            return proxy_url.split(':')[1].rstrip('/')
        return '80'
