"""Java/SpringBoot installer."""
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Optional
import xml.etree.ElementTree as ET
from .base import BaseInstaller


class JavaInstaller(BaseInstaller):
    """Installer for Java and Maven/Gradle projects."""

    JAVA_DOWNLOAD_URLS = {
        '17': 'https://download.oracle.com/java/17/latest/jdk-17_windows-x64_bin.zip',
        '11': 'https://download.oracle.com/java/11/latest/jdk-11_windows-x64_bin.zip'
    }

    # Multiple Maven download URLs as fallback
    MAVEN_URLS = [
        'https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.zip',
        'https://archive.apache.org/dist/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.zip',
        'https://mirrors.estointernet.in/apache/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.zip'
    ]

    def detect_version(self) -> Optional[str]:
        """Detect Java version from pom.xml or build.gradle."""
        pom_file = self.project_path / 'pom.xml'
        if pom_file.exists():
            return self._detect_from_pom(pom_file)

        gradle_file = self.project_path / 'build.gradle'
        if gradle_file.exists():
            return self._detect_from_gradle(gradle_file)

        return '17'  # Default to Java 17

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

        except Exception:
            pass

        return '17'

    def _detect_from_gradle(self, gradle_file: Path) -> str:
        """Extract Java version from build.gradle."""
        try:
            content = gradle_file.read_text(encoding='utf-8')
            if 'sourceCompatibility' in content:
                for line in content.split('\n'):
                    if 'sourceCompatibility' in line and '=' in line:
                        version = line.split('=')[1].strip().strip("'\"")
                        return version
        except Exception:
            pass

        return '17'

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
        print("Installing Java...")
        version = self.detect_version()

        # Use version 17 if specific version not available
        download_version = version if version in self.JAVA_DOWNLOAD_URLS else '17'

        tools_dir = Path.home() / '.dev-start' / 'tools'
        java_dir = tools_dir / f'jdk-{download_version}'

        if not java_dir.exists():
            print(f"Downloading Java {download_version}...")
            zip_path = tools_dir / f'jdk-{download_version}.zip'

            if not self.download_file(self.JAVA_DOWNLOAD_URLS[download_version], zip_path):
                print("Failed to download Java. Please install manually.")
                return False

            print("Extracting Java...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tools_dir)
            zip_path.unlink()

        # Set JAVA_HOME
        java_home = str(java_dir)
        java_bin = f"{java_home}\\bin"

        # Set environment variables for persistence
        self.env_manager.append_to_env('JAVA_HOME', java_home)
        self.env_manager.set_system_path(java_bin)

        # Update current process environment
        os.environ['JAVA_HOME'] = java_home
        if 'PATH' in os.environ:
            if java_bin not in os.environ['PATH']:
                os.environ['PATH'] = f"{java_bin}{os.pathsep}{os.environ['PATH']}"
        else:
            os.environ['PATH'] = java_bin

        print("✓ Java environment variables configured")
        print(f"  JAVA_HOME: {java_home}")
        print(f"  PATH: {java_bin} (added)")

        # Install Maven if pom.xml exists
        if (self.project_path / 'pom.xml').exists():
            return self._install_maven(tools_dir)

        return True

    def _install_maven(self, tools_dir: Path) -> bool:
        """Install Apache Maven with fallback URLs."""
        maven_dir = tools_dir / 'maven'

        if not maven_dir.exists():
            print("Downloading Maven...")
            zip_path = tools_dir / 'maven.zip'

            # Try each URL until one succeeds
            download_success = False
            for url in self.MAVEN_URLS:
                print(f"Trying: {url}")
                if self.download_file(url, zip_path):
                    download_success = True
                    print("✓ Maven downloaded successfully")
                    break
                else:
                    print(f"✗ Failed to download from this mirror, trying next...")

            if not download_success:
                print("✗ Failed to download Maven from all mirrors.")
                print("Please install Maven manually from: https://maven.apache.org/download.cgi")
                return False

            try:
                print("Extracting Maven...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tools_dir)

                # Rename extracted directory
                extracted_dir = None
                for item in tools_dir.iterdir():
                    if item.is_dir() and item.name.startswith('apache-maven'):
                        extracted_dir = item
                        print(f"Found extracted directory: {item.name}")
                        item.rename(maven_dir)
                        print(f"Renamed to: maven")
                        break

                if not extracted_dir:
                    print("✗ Could not find extracted Maven directory")
                    # List what was extracted
                    print("Contents of tools directory:")
                    for item in tools_dir.iterdir():
                        print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
                    return False

                zip_path.unlink()
                print("✓ Maven extracted successfully")

                # Verify Maven bin directory
                maven_bin = maven_dir / 'bin'
                if maven_bin.exists():
                    print(f"✓ Maven bin directory found: {maven_bin}")
                    # List bin contents
                    bin_files = list(maven_bin.iterdir())
                    print(f"  Found {len(bin_files)} files in bin/")
                    for f in bin_files[:5]:  # Show first 5 files
                        print(f"    - {f.name}")
                else:
                    print(f"✗ Maven bin directory not found at: {maven_bin}")
                    print("Maven directory contents:")
                    for item in maven_dir.iterdir():
                        print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

            except Exception as e:
                print(f"✗ Failed to extract Maven: {e}")
                import traceback
                traceback.print_exc()
                return False

        # Set Maven environment
        maven_home = str(maven_dir)
        maven_bin = f"{maven_dir}\\bin"

        # Set environment variables for persistence
        self.env_manager.append_to_env('MAVEN_HOME', maven_home)
        self.env_manager.set_system_path(maven_bin)

        # Update current process environment
        os.environ['MAVEN_HOME'] = maven_home
        if 'PATH' in os.environ:
            if maven_bin not in os.environ['PATH']:
                os.environ['PATH'] = f"{maven_bin}{os.pathsep}{os.environ['PATH']}"
        else:
            os.environ['PATH'] = maven_bin

        print("\n✓ Maven environment variables configured")
        print(f"  MAVEN_HOME: {maven_home}")
        print(f"  PATH: {maven_bin} (added)")

        return True

    def configure(self) -> bool:
        """Configure Java project."""
        print("Configuring Java project...")

        # Initialize Maven availability flag
        maven_available = False

        # Check and install Maven if needed (for Maven projects)
        if (self.project_path / 'pom.xml').exists():
            if not self.is_maven_installed():
                print("\nMaven not found. Installing Maven...")
                tools_dir = Path.home() / '.dev-start' / 'tools'
                tools_dir.mkdir(parents=True, exist_ok=True)
                if self._install_maven(tools_dir):
                    maven_available = True
                    print("\n✓ Maven installed successfully")
                else:
                    print("\n⚠ Warning: Failed to install Maven")
                    print("⚠ Skipping dependency installation - please install Maven manually")
                    maven_available = False
            else:
                print("\n✓ Maven is already installed")
                maven_available = True

            # Ensure .m2 directory exists only if Maven is available
            if maven_available:
                self._ensure_maven_directories()

        # Create application.properties if it doesn't exist (for Spring Boot)
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

        # Run Maven clean install to download all dependencies (only if Maven is available)
        build_success = False
        if (self.project_path / 'pom.xml').exists() and maven_available:
            print("\nInstalling project dependencies with Maven...")
            if self._run_maven_install():
                build_success = True
            else:
                print("⚠ Warning: Maven install failed, but continuing...")
        elif (self.project_path / 'pom.xml').exists() and not maven_available:
            print("\n⚠ Skipping Maven dependency installation (Maven not available)")

        # Run Gradle build for Gradle projects
        if (self.project_path / 'build.gradle').exists():
            print("\nInstalling project dependencies with Gradle...")
            if self._run_gradle_build():
                build_success = True
            else:
                print("⚠ Warning: Gradle build failed, but continuing...")

        # Validate build artifacts
        if build_success:
            self._validate_build()

        return True

    def _validate_build(self):
        """Validate that build artifacts were created successfully."""
        print("\n" + "=" * 60)
        print("Build Validation")
        print("=" * 60)

        # Check for Maven build artifacts
        target_dir = self.project_path / 'target'
        if target_dir.exists():
            # Look for JAR files
            jar_files = list(target_dir.glob('*.jar'))
            if jar_files:
                print(f"✓ Build artifacts found:")
                for jar in jar_files:
                    size_mb = jar.stat().st_size / (1024 * 1024)
                    print(f"  - {jar.name} ({size_mb:.2f} MB)")
                print(f"\n✓ Application is ready to run!")
                print(f"  To run: cd {self.project_path} && java -jar target/{jar_files[0].name}")
            else:
                print("⚠ No JAR files found in target directory")

        # Check for Gradle build artifacts
        build_dir = self.project_path / 'build'
        if build_dir.exists():
            libs_dir = build_dir / 'libs'
            if libs_dir.exists():
                jar_files = list(libs_dir.glob('*.jar'))
                if jar_files:
                    print(f"✓ Build artifacts found:")
                    for jar in jar_files:
                        size_mb = jar.stat().st_size / (1024 * 1024)
                        print(f"  - {jar.name} ({size_mb:.2f} MB)")
                    print(f"\n✓ Application is ready to run!")
                    print(f"  To run: cd {self.project_path} && java -jar build/libs/{jar_files[0].name}")

        print("=" * 60)

    def _run_maven_install(self) -> bool:
        """Run Maven clean install to download dependencies."""
        # Try to find Maven executable
        print("\nSearching for Maven executable...")
        maven_cmd = self._find_maven_executable()

        if not maven_cmd:
            print("\n✗ Maven (mvn) not found in PATH or installation directory")
            print("  Checked locations:")
            tools_dir = Path.home() / '.dev-start' / 'tools'
            maven_dir = tools_dir / 'maven'
            print(f"    - {maven_dir / 'bin' / 'mvn.cmd'}")
            print(f"    - {maven_dir / 'bin' / 'mvn.bat'}")
            print(f"    - {maven_dir / 'bin' / 'mvn'}")
            print(f"    - PATH")
            return False

        try:
            # Show the full command being executed
            cmd_display = f"{Path(maven_cmd).name} clean install -DskipTests"
            print(f"\nRunning: {cmd_display}")
            print(f"  Full path: {maven_cmd}")

            result = subprocess.run(
                [maven_cmd, 'clean', 'install', '-DskipTests'],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            if result.returncode == 0:
                print("\n✓ Maven dependencies installed successfully")
                print("✓ Project built successfully")
                return True
            else:
                print(f"\n✗ Maven install failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr[:500]}")  # Print first 500 chars
                return False
        except subprocess.TimeoutExpired:
            print("\n✗ Maven install timed out after 10 minutes")
            return False
        except FileNotFoundError as e:
            print(f"\n✗ Maven executable not found: {maven_cmd}")
            print(f"  Error: {e}")
            return False
        except Exception as e:
            print(f"\n✗ Error running Maven: {e}")
            return False

    def _find_maven_executable(self) -> Optional[str]:
        """Find Maven executable in PATH or installation directory."""
        import shutil

        # First, try the installation directory (most reliable for just-installed Maven)
        tools_dir = Path.home() / '.dev-start' / 'tools'
        maven_dir = tools_dir / 'maven'

        # Try mvn.cmd (Windows)
        mvn_cmd = maven_dir / 'bin' / 'mvn.cmd'
        if mvn_cmd.exists():
            print(f"Found Maven at: {mvn_cmd}")
            return str(mvn_cmd)

        # Try mvn.bat (Windows alternative)
        mvn_bat = maven_dir / 'bin' / 'mvn.bat'
        if mvn_bat.exists():
            print(f"Found Maven at: {mvn_bat}")
            return str(mvn_bat)

        # Try mvn (Unix-like)
        mvn_unix = maven_dir / 'bin' / 'mvn'
        if mvn_unix.exists():
            print(f"Found Maven at: {mvn_unix}")
            return str(mvn_unix)

        # If not in installation directory, try to find mvn in PATH
        mvn_in_path = shutil.which('mvn')
        if mvn_in_path:
            print(f"Found Maven in PATH: {mvn_in_path}")
            return mvn_in_path

        return None

    def _run_gradle_build(self) -> bool:
        """Run Gradle build to download dependencies."""
        try:
            # Try gradlew first (Windows)
            gradle_cmd = 'gradlew.bat' if (self.project_path / 'gradlew.bat').exists() else 'gradle'
            print(f"Running: {gradle_cmd} build -x test")

            result = subprocess.run(
                [gradle_cmd, 'build', '-x', 'test'],
                cwd=str(self.project_path),
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )

            if result.returncode == 0:
                print("✓ Gradle dependencies installed successfully")
                return True
            else:
                print(f"✗ Gradle build failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr[:500]}")
                return False
        except subprocess.TimeoutExpired:
            print("✗ Gradle build timed out after 10 minutes")
            return False
        except FileNotFoundError:
            print(f"✗ {gradle_cmd} not found")
            return False
        except Exception as e:
            print(f"✗ Error running Gradle: {e}")
            return False

    def _ensure_maven_directories(self):
        """Ensure Maven directories exist."""
        maven_home = Path.home() / '.m2'
        maven_home.mkdir(exist_ok=True)
        print(f"\n✓ Maven directory created/verified: {maven_home}")

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
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(default_settings)
            print(f"✓ Created Maven settings.xml: {settings_file}")

    def _configure_maven_proxy(self):
        """Configure Maven proxy settings."""
        maven_dir = Path.home() / '.m2'
        maven_dir.mkdir(exist_ok=True)
        settings_file = maven_dir / 'settings.xml'

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
      <host>{self._get_proxy_host(self.proxy_manager.http_proxy)}</host>
      <port>{self._get_proxy_port(self.proxy_manager.http_proxy)}</port>
    </proxy>
  </proxies>
</settings>
"""
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write(proxy_config)
        print(f"✓ Maven proxy configured in settings.xml")

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
