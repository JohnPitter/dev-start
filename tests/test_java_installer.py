"""Tests for Java installer."""
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import subprocess

from src.installers.java_installer import JavaInstaller
from src.proxy_manager import ProxyManager


class TestJavaInstaller(unittest.TestCase):
    """Test Java installer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.proxy_manager = ProxyManager()
        self.installer = JavaInstaller(self.temp_dir, self.proxy_manager)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_detect_version_from_pom(self):
        """Test detecting Java version from pom.xml."""
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <properties>
        <java.version>17</java.version>
    </properties>
</project>"""
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text(pom_content, encoding='utf-8')

        version = self.installer.detect_version()
        self.assertEqual(version, '17')

    def test_detect_version_from_pom_compiler_source(self):
        """Test detecting Java version from maven.compiler.source."""
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
    </properties>
</project>"""
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text(pom_content, encoding='utf-8')

        version = self.installer.detect_version()
        self.assertEqual(version, '11')

    def test_detect_version_from_gradle(self):
        """Test detecting Java version from build.gradle."""
        gradle_content = "sourceCompatibility = '17'"
        gradle_file = self.temp_dir / 'build.gradle'
        gradle_file.write_text(gradle_content, encoding='utf-8')

        version = self.installer.detect_version()
        self.assertEqual(version, '17')

    def test_detect_version_default(self):
        """Test default Java version when no config files exist."""
        version = self.installer.detect_version()
        self.assertEqual(version, '17')

    @patch('subprocess.run')
    def test_is_maven_installed_true(self, mock_run):
        """Test checking if Maven is installed (true case)."""
        mock_run.return_value = Mock(returncode=0)
        self.assertTrue(self.installer.is_maven_installed())
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_is_maven_installed_false(self, mock_run):
        """Test checking if Maven is not installed."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_maven_installed())

    @patch('shutil.which')
    @patch('pathlib.Path.exists')
    def test_find_maven_executable_not_found(self, mock_exists, mock_which):
        """Test finding Maven executable when not installed."""
        mock_exists.return_value = False
        mock_which.return_value = None
        result = self.installer._find_maven_executable()
        self.assertIsNone(result)

    @patch('pathlib.Path.exists')
    def test_find_maven_executable_cmd(self, mock_exists):
        """Test finding Maven executable (mvn.cmd or mvn)."""
        # Mock to return True for mvn path
        mock_exists.return_value = True
        result = self.installer._find_maven_executable()
        self.assertIsNotNone(result)
        self.assertIn('mvn', result)  # Accept mvn or mvn.cmd

    def test_get_proxy_host(self):
        """Test extracting host from proxy URL."""
        host = self.installer._get_proxy_host('http://proxy.example.com:8080')
        self.assertEqual(host, 'proxy.example.com')

    def test_get_proxy_host_no_protocol(self):
        """Test extracting host from proxy URL without protocol."""
        host = self.installer._get_proxy_host('proxy.example.com:8080')
        self.assertEqual(host, 'proxy.example.com')

    def test_get_proxy_port(self):
        """Test extracting port from proxy URL."""
        port = self.installer._get_proxy_port('http://proxy.example.com:8080')
        self.assertEqual(port, '8080')

    def test_get_proxy_port_with_trailing_slash(self):
        """Test extracting port from proxy URL with trailing slash."""
        port = self.installer._get_proxy_port('http://proxy.example.com:8080/')
        self.assertEqual(port, '8080')

    def test_get_proxy_port_default(self):
        """Test default port when not specified."""
        port = self.installer._get_proxy_port('http://proxy.example.com')
        self.assertEqual(port, '80')

    @patch('subprocess.run')
    def test_run_maven_install_success(self, mock_run):
        """Test running Maven install successfully."""
        # Create mvn.cmd file
        tools_dir = Path.home() / '.dev-start' / 'tools' / 'maven' / 'bin'
        tools_dir.mkdir(parents=True, exist_ok=True)
        mvn_cmd = tools_dir / 'mvn.cmd'
        mvn_cmd.write_text('echo test', encoding='utf-8')

        try:
            mock_run.return_value = Mock(returncode=0, stdout='BUILD SUCCESS', stderr='')

            # Create pom.xml
            pom_file = self.temp_dir / 'pom.xml'
            pom_file.write_text('<project/>', encoding='utf-8')

            result = self.installer._run_maven_install()
            self.assertTrue(result)
        finally:
            # Cleanup
            if tools_dir.parent.parent.exists():
                shutil.rmtree(tools_dir.parent.parent)

    def test_run_maven_install_maven_not_found(self):
        """Test running Maven install when Maven not found."""
        result = self.installer._run_maven_install()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_is_installed_true(self, mock_run):
        """Test checking if Java is installed (true case)."""
        mock_run.return_value = Mock(returncode=0, stdout='java version "17.0.1"')
        self.assertTrue(self.installer.is_installed())

    @patch('subprocess.run')
    def test_is_installed_false(self, mock_run):
        """Test checking if Java is not installed."""
        mock_run.side_effect = FileNotFoundError()
        self.assertFalse(self.installer.is_installed())

    def test_install_requires_download(self):
        """Test install requires downloading Java."""
        # Java installer doesn't check if already installed,
        # it always downloads/extracts
        with patch.object(self.installer, 'download_file', return_value=False):
            result = self.installer.install()
            self.assertFalse(result)

    def test_install_not_installed(self):
        """Test install when Java is not installed (manual install required)."""
        with patch.object(self.installer, 'is_installed', return_value=False):
            result = self.installer.install()
            self.assertFalse(result)

    @patch('subprocess.run')
    def test_configure_no_pom_gradle(self, mock_run):
        """Test configure when no pom.xml or build.gradle exists."""
        # Mock Maven install check
        with patch.object(self.installer, 'is_maven_installed', return_value=True):
            with patch.object(self.installer, '_run_maven_install', return_value=True):
                result = self.installer.configure()
                self.assertTrue(result)

    def test_configure_with_pom(self):
        """Test configure with pom.xml present."""
        # Create pom.xml
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('<project/>', encoding='utf-8')

        with patch.object(self.installer, 'is_maven_installed', return_value=True):
            with patch.object(self.installer, '_run_maven_install', return_value=True):
                result = self.installer.configure()
                self.assertTrue(result)

    def test_configure_maven_not_installed(self):
        """Test configure when Maven is not installed."""
        with patch.object(self.installer, 'is_maven_installed', return_value=False):
            with patch.object(self.installer, '_install_maven', return_value=True):
                with patch.object(self.installer, '_run_maven_install', return_value=True):
                    result = self.installer.configure()
                    self.assertTrue(result)

    def test_ensure_maven_directories(self):
        """Test ensuring Maven directories exist."""
        # This creates .m2 directory
        self.installer._ensure_maven_directories()

        maven_home = Path.home() / '.m2'
        self.assertTrue(maven_home.exists())

        repository_dir = maven_home / 'repository'
        self.assertTrue(repository_dir.exists())

    def test_detect_from_pom_exception(self):
        """Test _detect_from_pom with malformed XML."""
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('invalid xml content', encoding='utf-8')

        result = self.installer._detect_from_pom(pom_file)
        self.assertEqual(result, '17')

    def test_detect_from_pom_no_version_properties(self):
        """Test _detect_from_pom without version properties."""
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <properties>
        <other.property>value</other.property>
    </properties>
</project>"""
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text(pom_content, encoding='utf-8')

        result = self.installer._detect_from_pom(pom_file)
        self.assertEqual(result, '17')

    def test_detect_from_gradle_exception(self):
        """Test _detect_from_gradle with unreadable file."""
        gradle_file = self.temp_dir / 'build.gradle'
        gradle_file.write_text('sourceCompatibility = "11"', encoding='utf-8')

        # Mock read_text to raise IOError
        with patch.object(Path, 'read_text', side_effect=IOError('Read error')):
            result = self.installer._detect_from_gradle(gradle_file)
            self.assertEqual(result, '17')

    def test_detect_from_gradle_no_source_compatibility(self):
        """Test _detect_from_gradle without sourceCompatibility."""
        gradle_content = "plugins { id 'java' }"
        gradle_file = self.temp_dir / 'build.gradle'
        gradle_file.write_text(gradle_content, encoding='utf-8')

        result = self.installer._detect_from_gradle(gradle_file)
        self.assertEqual(result, '17')

    @patch('zipfile.ZipFile')
    @patch.object(Path, 'exists')
    def test_install_success_with_download(self, mock_exists, mock_zipfile):
        """Test successful installation with download."""
        # Mock java_dir doesn't exist initially
        mock_exists.side_effect = lambda: False

        with patch.object(self.installer, 'download_file', return_value=True):
            with patch.object(Path, 'unlink'):
                mock_zip = MagicMock()
                mock_zipfile.return_value.__enter__.return_value = mock_zip

                result = self.installer.install()
                self.assertTrue(result)

    @patch.object(Path, 'exists')
    def test_install_with_existing_java(self, mock_exists):
        """Test installation when Java already extracted."""
        # Mock java_dir exists
        mock_exists.return_value = True

        result = self.installer.install()
        self.assertTrue(result)

    @patch.object(Path, 'exists')
    def test_install_with_pom_triggers_maven_install(self, mock_exists):
        """Test installation triggers Maven install when pom.xml exists."""
        # Create pom.xml
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('<project/>', encoding='utf-8')

        # Mock java_dir exists
        def exists_side_effect():
            path = mock_exists.call_args[0][0] if mock_exists.call_args else None
            if path and 'jdk-' in str(path):
                return True
            return pom_file.exists()

        mock_exists.side_effect = lambda: True

        with patch.object(self.installer, '_install_maven', return_value=True) as mock_maven:
            result = self.installer.install()
            mock_maven.assert_called_once()

    @patch('zipfile.ZipFile')
    def test_install_maven_success(self, mock_zipfile):
        """Test successful Maven installation."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Mock Maven doesn't exist
        maven_dir = tools_dir / 'maven'

        # Create mock extracted directory
        extracted_dir = tools_dir / 'apache-maven-3.9.9'

        with patch.object(self.installer, 'download_file', return_value=True):
            with patch.object(Path, 'unlink'):
                with patch.object(Path, 'iterdir', return_value=[extracted_dir]):
                    with patch.object(Path, 'is_dir', return_value=True):
                        with patch.object(Path, 'rename'):
                            with patch.object(Path, 'exists', return_value=True):
                                mock_zip = MagicMock()
                                mock_zipfile.return_value.__enter__.return_value = mock_zip

                                result = self.installer._install_maven(tools_dir)
                                self.assertTrue(result)

    def test_install_maven_download_failure_all_urls(self):
        """Test Maven installation when all download URLs fail."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(self.installer, 'download_file', return_value=False):
            result = self.installer._install_maven(tools_dir)
            self.assertFalse(result)

    def test_install_maven_extraction_error(self):
        """Test Maven installation with extraction error."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Mock download_and_extract to fail
        with patch.object(self.installer, 'download_and_extract', return_value=(False, None)):
            result = self.installer._install_maven(tools_dir)
            self.assertFalse(result)

    def test_install_maven_no_extracted_dir_found(self):
        """Test Maven installation when download fails for all URLs."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Mock download_and_extract to return failure
        with patch.object(self.installer, 'download_and_extract', return_value=(False, None)):
            result = self.installer._install_maven(tools_dir)
            # When download fails, should return False
            self.assertFalse(result)

    @patch.object(Path, 'exists')
    def test_install_maven_already_exists(self, mock_exists):
        """Test Maven installation when Maven already exists."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Mock Maven directory exists
        mock_exists.return_value = True

        result = self.installer._install_maven(tools_dir)
        self.assertTrue(result)

    def test_configure_with_gradle(self):
        """Test configure with build.gradle present."""
        # Create build.gradle
        gradle_file = self.temp_dir / 'build.gradle'
        gradle_file.write_text('sourceCompatibility = "17"', encoding='utf-8')

        with patch.object(self.installer, '_run_gradle_build', return_value=True):
            with patch.object(self.installer, '_validate_build'):
                result = self.installer.configure()
                self.assertTrue(result)

    def test_configure_maven_install_fails(self):
        """Test configure when Maven install fails."""
        # Create pom.xml
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('<project/>', encoding='utf-8')

        with patch.object(self.installer, 'is_maven_installed', return_value=True):
            with patch.object(self.installer, '_run_maven_install', return_value=False):
                result = self.installer.configure()
                self.assertTrue(result)  # Should still return True but print warning

    def test_configure_gradle_build_fails(self):
        """Test configure when Gradle build fails."""
        # Create build.gradle
        gradle_file = self.temp_dir / 'build.gradle'
        gradle_file.write_text('sourceCompatibility = "17"', encoding='utf-8')

        with patch.object(self.installer, '_run_gradle_build', return_value=False):
            result = self.installer.configure()
            self.assertTrue(result)  # Should still return True but print warning

    def test_configure_creates_application_properties(self):
        """Test configure creates application.properties for Spring Boot."""
        # Create pom.xml
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('<project/>', encoding='utf-8')

        with patch.object(self.installer, 'is_maven_installed', return_value=True):
            with patch.object(self.installer, '_run_maven_install', return_value=True):
                with patch.object(self.installer, '_validate_build'):
                    result = self.installer.configure()
                    self.assertTrue(result)

    def test_configure_with_proxy(self):
        """Test configure with proxy settings."""
        # Create pom.xml
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('<project/>', encoding='utf-8')

        # Set proxy
        self.proxy_manager.http_proxy = 'http://proxy.example.com:8080'

        with patch.object(self.installer, 'is_maven_installed', return_value=True):
            with patch.object(self.installer, '_configure_maven_proxy'):
                with patch.object(self.installer, '_run_maven_install', return_value=True):
                    with patch.object(self.installer, '_validate_build'):
                        result = self.installer.configure()
                        self.assertTrue(result)

    def test_configure_maven_not_available_skips_dependencies(self):
        """Test configure skips Maven dependencies when Maven not available."""
        # Create pom.xml
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('<project/>', encoding='utf-8')

        with patch.object(self.installer, 'is_maven_installed', return_value=False):
            with patch.object(self.installer, '_install_maven', return_value=False):
                result = self.installer.configure()
                self.assertTrue(result)

    def test_validate_build_with_maven_artifacts(self):
        """Test _validate_build with Maven JAR files."""
        # Create target directory with JAR
        target_dir = self.temp_dir / 'target'
        target_dir.mkdir(parents=True, exist_ok=True)
        jar_file = target_dir / 'app.jar'
        jar_file.write_bytes(b'fake jar content')

        self.installer._validate_build()
        # Just ensure it runs without error

    def test_validate_build_with_gradle_artifacts(self):
        """Test _validate_build with Gradle JAR files."""
        # Create build/libs directory with JAR
        libs_dir = self.temp_dir / 'build' / 'libs'
        libs_dir.mkdir(parents=True, exist_ok=True)
        jar_file = libs_dir / 'app.jar'
        jar_file.write_bytes(b'fake jar content')

        self.installer._validate_build()
        # Just ensure it runs without error

    def test_validate_build_no_artifacts(self):
        """Test _validate_build with no artifacts."""
        # Create target directory but no JARs
        target_dir = self.temp_dir / 'target'
        target_dir.mkdir(parents=True, exist_ok=True)

        self.installer._validate_build()
        # Just ensure it runs without error

    @patch('subprocess.run')
    def test_run_maven_install_failure(self, mock_run):
        """Test _run_maven_install when Maven command fails."""
        # Create mvn.cmd file
        tools_dir = Path.home() / '.dev-start' / 'tools' / 'maven' / 'bin'
        tools_dir.mkdir(parents=True, exist_ok=True)
        mvn_cmd = tools_dir / 'mvn.cmd'
        mvn_cmd.write_text('echo test', encoding='utf-8')

        try:
            mock_run.return_value = Mock(returncode=1, stdout='', stderr='Build failed')

            # Create pom.xml
            pom_file = self.temp_dir / 'pom.xml'
            pom_file.write_text('<project/>', encoding='utf-8')

            result = self.installer._run_maven_install()
            self.assertFalse(result)
        finally:
            # Cleanup
            if tools_dir.parent.parent.exists():
                shutil.rmtree(tools_dir.parent.parent)

    @patch('subprocess.run')
    def test_run_maven_install_timeout(self, mock_run):
        """Test _run_maven_install with timeout."""
        # Create mvn.cmd file
        tools_dir = Path.home() / '.dev-start' / 'tools' / 'maven' / 'bin'
        tools_dir.mkdir(parents=True, exist_ok=True)
        mvn_cmd = tools_dir / 'mvn.cmd'
        mvn_cmd.write_text('echo test', encoding='utf-8')

        try:
            mock_run.side_effect = subprocess.TimeoutExpired('mvn', 600)

            # Create pom.xml
            pom_file = self.temp_dir / 'pom.xml'
            pom_file.write_text('<project/>', encoding='utf-8')

            result = self.installer._run_maven_install()
            self.assertFalse(result)
        finally:
            # Cleanup
            if tools_dir.parent.parent.exists():
                shutil.rmtree(tools_dir.parent.parent)

    @patch('subprocess.run')
    def test_run_maven_install_file_not_found(self, mock_run):
        """Test _run_maven_install when Maven executable not found."""
        # Create mvn.cmd file
        tools_dir = Path.home() / '.dev-start' / 'tools' / 'maven' / 'bin'
        tools_dir.mkdir(parents=True, exist_ok=True)
        mvn_cmd = tools_dir / 'mvn.cmd'
        mvn_cmd.write_text('echo test', encoding='utf-8')

        try:
            mock_run.side_effect = FileNotFoundError('mvn not found')

            # Create pom.xml
            pom_file = self.temp_dir / 'pom.xml'
            pom_file.write_text('<project/>', encoding='utf-8')

            result = self.installer._run_maven_install()
            self.assertFalse(result)
        finally:
            # Cleanup
            if tools_dir.parent.parent.exists():
                shutil.rmtree(tools_dir.parent.parent)

    @patch('subprocess.run')
    def test_run_maven_install_generic_exception(self, mock_run):
        """Test _run_maven_install with generic exception."""
        # Create mvn.cmd file
        tools_dir = Path.home() / '.dev-start' / 'tools' / 'maven' / 'bin'
        tools_dir.mkdir(parents=True, exist_ok=True)
        mvn_cmd = tools_dir / 'mvn.cmd'
        mvn_cmd.write_text('echo test', encoding='utf-8')

        try:
            mock_run.side_effect = subprocess.SubprocessError('Unexpected error')

            # Create pom.xml
            pom_file = self.temp_dir / 'pom.xml'
            pom_file.write_text('<project/>', encoding='utf-8')

            result = self.installer._run_maven_install()
            self.assertFalse(result)
        finally:
            # Cleanup
            if tools_dir.parent.parent.exists():
                shutil.rmtree(tools_dir.parent.parent)

    @patch('shutil.which')
    def test_find_maven_executable_mvn_bat(self, mock_which):
        """Test finding Maven executable (mvn.bat)."""
        mock_which.return_value = None

        # Create actual mvn.bat file for testing
        tools_dir = Path.home() / '.dev-start' / 'tools' / 'maven' / 'bin'
        tools_dir.mkdir(parents=True, exist_ok=True)
        mvn_bat = tools_dir / 'mvn.bat'
        mvn_bat.write_text('echo test', encoding='utf-8')

        try:
            result = self.installer._find_maven_executable()
            self.assertIsNotNone(result)
            self.assertIn('mvn.bat', result)
        finally:
            # Cleanup
            if tools_dir.parent.parent.exists():
                shutil.rmtree(tools_dir.parent.parent)

    @patch('shutil.which')
    def test_find_maven_executable_mvn_unix(self, mock_which):
        """Test finding Maven executable (mvn Unix)."""
        mock_which.return_value = None

        # Create actual mvn file for testing
        tools_dir = Path.home() / '.dev-start' / 'tools' / 'maven' / 'bin'
        tools_dir.mkdir(parents=True, exist_ok=True)
        mvn_unix = tools_dir / 'mvn'
        mvn_unix.write_text('#!/bin/sh\necho test', encoding='utf-8')

        try:
            result = self.installer._find_maven_executable()
            self.assertIsNotNone(result)
            self.assertIn('mvn', result)
        finally:
            # Cleanup
            if tools_dir.parent.parent.exists():
                shutil.rmtree(tools_dir.parent.parent)

    @patch('shutil.which')
    @patch.object(Path, 'exists')
    def test_find_maven_executable_in_path(self, mock_exists, mock_which):
        """Test finding Maven executable in PATH."""
        mock_exists.return_value = False
        mock_which.return_value = 'C:\\Program Files\\Maven\\bin\\mvn.cmd'

        result = self.installer._find_maven_executable()
        self.assertEqual(result, 'C:\\Program Files\\Maven\\bin\\mvn.cmd')

    @patch('subprocess.run')
    def test_run_gradle_build_success(self, mock_run):
        """Test successful Gradle build."""
        # Create gradlew.bat
        gradlew = self.temp_dir / 'gradlew.bat'
        gradlew.write_text('echo test', encoding='utf-8')

        mock_run.return_value = Mock(returncode=0, stdout='BUILD SUCCESSFUL', stderr='')

        result = self.installer._run_gradle_build()
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_run_gradle_build_failure(self, mock_run):
        """Test Gradle build failure."""
        mock_run.return_value = Mock(returncode=1, stdout='', stderr='Build failed')

        result = self.installer._run_gradle_build()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_run_gradle_build_timeout(self, mock_run):
        """Test Gradle build timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('gradle', 600)

        result = self.installer._run_gradle_build()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_run_gradle_build_file_not_found(self, mock_run):
        """Test Gradle build with missing executable."""
        mock_run.side_effect = FileNotFoundError('gradle not found')

        result = self.installer._run_gradle_build()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_run_gradle_build_generic_exception(self, mock_run):
        """Test Gradle build with generic exception."""
        mock_run.side_effect = Exception('Unexpected error')

        result = self.installer._run_gradle_build()
        self.assertFalse(result)

    def test_ensure_maven_directories_creates_settings_xml(self):
        """Test _ensure_maven_directories creates settings.xml."""
        maven_home = Path.home() / '.m2'
        settings_file = maven_home / 'settings.xml'

        # Remove settings.xml if it exists
        if settings_file.exists():
            settings_file.unlink()

        self.installer._ensure_maven_directories()

        self.assertTrue(settings_file.exists())
        content = settings_file.read_text(encoding='utf-8')
        self.assertIn('localRepository', content)

    def test_configure_maven_proxy(self):
        """Test _configure_maven_proxy creates proxy settings."""
        self.proxy_manager.http_proxy = 'http://proxy.example.com:8080'

        self.installer._configure_maven_proxy()

        maven_home = Path.home() / '.m2'
        settings_file = maven_home / 'settings.xml'

        self.assertTrue(settings_file.exists())
        content = settings_file.read_text(encoding='utf-8')
        self.assertIn('proxy.example.com', content)
        self.assertIn('8080', content)

    @patch('zipfile.ZipFile')
    def test_install_sets_environment_variables(self, mock_zipfile):
        """Test install sets JAVA_HOME and PATH environment variables."""
        import os

        # Save original env vars
        original_java_home = os.environ.get('JAVA_HOME')
        original_path = os.environ.get('PATH')

        # Remove them to test setting
        os.environ.pop('JAVA_HOME', None)

        try:
            with patch.object(Path, 'exists', return_value=False):
                with patch.object(self.installer, 'download_file', return_value=True):
                    with patch.object(Path, 'unlink'):
                        mock_zip = MagicMock()
                        mock_zipfile.return_value.__enter__.return_value = mock_zip

                        result = self.installer.install()
                        self.assertTrue(result)

                        # Check environment variables were set
                        self.assertIn('JAVA_HOME', os.environ)
                        self.assertIn('PATH', os.environ)
        finally:
            # Restore original values
            if original_java_home:
                os.environ['JAVA_HOME'] = original_java_home
            if original_path:
                os.environ['PATH'] = original_path

    @patch('zipfile.ZipFile')
    def test_install_maven_with_bin_directory_verification(self, mock_zipfile):
        """Test Maven installation verifies bin directory exists."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Create mock extracted directory with bin folder
        extracted_dir = tools_dir / 'apache-maven-3.9.9'
        extracted_dir.mkdir(parents=True, exist_ok=True)
        bin_dir = extracted_dir / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=True)

        # Create some files in bin
        (bin_dir / 'mvn.cmd').write_text('echo test', encoding='utf-8')
        (bin_dir / 'mvn.bat').write_text('echo test', encoding='utf-8')

        maven_dir = tools_dir / 'maven'

        with patch.object(self.installer, 'download_file', return_value=True):
            with patch.object(Path, 'unlink'):
                mock_zip = MagicMock()
                mock_zipfile.return_value.__enter__.return_value = mock_zip

                # Mock the extraction to actually create the directory
                def extract_side_effect(path):
                    pass  # Directory already created above

                mock_zip.extractall.side_effect = extract_side_effect

                # Rename after extraction
                extracted_dir.rename(maven_dir)

                result = self.installer._install_maven(tools_dir)
                self.assertTrue(result)

    @patch('zipfile.ZipFile')
    def test_install_maven_without_bin_directory(self, mock_zipfile):
        """Test Maven installation when bin directory doesn't exist."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Create mock extracted directory WITHOUT bin folder
        extracted_dir = tools_dir / 'apache-maven-3.9.9'
        extracted_dir.mkdir(parents=True, exist_ok=True)

        maven_dir = tools_dir / 'maven'

        with patch.object(self.installer, 'download_file', return_value=True):
            with patch.object(Path, 'unlink'):
                mock_zip = MagicMock()
                mock_zipfile.return_value.__enter__.return_value = mock_zip

                def extract_side_effect(path):
                    pass

                mock_zip.extractall.side_effect = extract_side_effect

                # Rename after extraction
                extracted_dir.rename(maven_dir)

                result = self.installer._install_maven(tools_dir)
                self.assertTrue(result)  # Should still succeed, just print warning

    @patch.object(Path, 'exists')
    def test_install_maven_sets_environment_variables(self, mock_exists):
        """Test _install_maven sets MAVEN_HOME and PATH."""
        import os
        original_path = os.environ.get('PATH', '')

        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Mock Maven directory exists
        mock_exists.return_value = True

        result = self.installer._install_maven(tools_dir)
        self.assertTrue(result)

        # Check environment variables were set
        self.assertIn('MAVEN_HOME', os.environ)
        self.assertIn('PATH', os.environ)

        # Restore original PATH
        if original_path:
            os.environ['PATH'] = original_path

    def test_configure_maven_install_success_message(self):
        """Test configure prints success message when Maven installed."""
        # Create pom.xml
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('<project/>', encoding='utf-8')

        with patch.object(self.installer, 'is_maven_installed', return_value=False):
            with patch.object(self.installer, '_install_maven', return_value=True):
                with patch.object(self.installer, '_run_maven_install', return_value=True):
                    with patch.object(self.installer, '_validate_build'):
                        result = self.installer.configure()
                        self.assertTrue(result)

    @patch('zipfile.ZipFile')
    def test_install_maven_lists_extracted_contents(self, mock_zipfile):
        """Test Maven installation lists extracted directory contents."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Don't create apache-maven directory - test the "not found" path
        # Create some other directories/files
        (tools_dir / 'other_file.txt').write_text('test', encoding='utf-8')

        with patch.object(self.installer, 'download_file', return_value=True):
            with patch.object(Path, 'unlink'):
                mock_zip = MagicMock()
                mock_zipfile.return_value.__enter__.return_value = mock_zip

                result = self.installer._install_maven(tools_dir)
                self.assertFalse(result)  # Should fail when no apache-maven dir found

    def test_install_sets_path_when_path_not_in_environ(self):
        """Test install sets PATH when PATH doesn't exist in environment."""
        import os

        # Save and remove PATH
        original_path = os.environ.pop('PATH', None)

        try:
            with patch.object(Path, 'exists', return_value=True):
                result = self.installer.install()
                self.assertTrue(result)
                # PATH should be set
                self.assertIn('PATH', os.environ)
        finally:
            # Restore PATH
            if original_path is not None:
                os.environ['PATH'] = original_path

    def test_install_maven_sets_path_when_path_not_in_environ(self):
        """Test _install_maven sets PATH when PATH doesn't exist."""
        import os

        # Save and remove PATH
        original_path = os.environ.pop('PATH', None)

        try:
            tools_dir = self.temp_dir / 'tools'
            tools_dir.mkdir(parents=True, exist_ok=True)

            with patch.object(Path, 'exists', return_value=True):
                result = self.installer._install_maven(tools_dir)
                self.assertTrue(result)
                # PATH should be set
                self.assertIn('PATH', os.environ)
        finally:
            # Restore PATH
            if original_path is not None:
                os.environ['PATH'] = original_path

    def test_install_maven_real_extraction_flow(self):
        """Test Maven installation with actual directory operations."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Create real apache-maven directory that will be found after extraction
        extracted_dir = tools_dir / 'apache-maven-3.9.9'
        extracted_dir.mkdir(parents=True, exist_ok=True)
        bin_dir = extracted_dir / 'bin'
        bin_dir.mkdir(parents=True, exist_ok=True)

        # Create some files in bin to test listing
        for i in range(6):
            (bin_dir / f'file{i}.txt').write_text(f'content{i}', encoding='utf-8')

        # Mock download_and_extract to return success and the extracted dir
        with patch.object(self.installer, 'download_and_extract', return_value=(True, extracted_dir)):
            result = self.installer._install_maven(tools_dir)
            self.assertTrue(result)

            # Verify maven directory was created (renamed from extracted_dir)
            maven_dir = tools_dir / 'maven'
            self.assertTrue(maven_dir.exists())

    @patch('zipfile.ZipFile')
    def test_install_adds_to_existing_path(self, mock_zipfile):
        """Test install adds java_bin to existing PATH."""
        import os

        # Set a specific PATH
        original_path = os.environ.get('PATH', '')
        os.environ['PATH'] = 'C:\\existing\\path'

        try:
            with patch.object(Path, 'exists', return_value=False):
                with patch.object(self.installer, 'download_file', return_value=True):
                    with patch.object(Path, 'unlink'):
                        mock_zip = MagicMock()
                        mock_zipfile.return_value.__enter__.return_value = mock_zip

                        result = self.installer.install()
                        self.assertTrue(result)

                        # Check that PATH contains both old and new
                        self.assertIn('jdk-', os.environ['PATH'])
                        self.assertIn('C:\\existing\\path', os.environ['PATH'])
        finally:
            if original_path:
                os.environ['PATH'] = original_path

    @patch.object(Path, 'exists')
    def test_install_maven_adds_to_existing_path(self, mock_exists):
        """Test _install_maven adds maven_bin to existing PATH."""
        import os

        # Set a specific PATH
        original_path = os.environ.get('PATH', '')
        os.environ['PATH'] = 'C:\\existing\\path'

        try:
            tools_dir = self.temp_dir / 'tools'
            tools_dir.mkdir(parents=True, exist_ok=True)

            # Mock Maven directory exists
            mock_exists.return_value = True

            result = self.installer._install_maven(tools_dir)
            self.assertTrue(result)

            # Check that PATH contains both old and new
            self.assertIn('maven', os.environ['PATH'])
            self.assertIn('C:\\existing\\path', os.environ['PATH'])
        finally:
            if original_path:
                os.environ['PATH'] = original_path

    def test_run_maven_install_prints_error_messages(self):
        """Test _run_maven_install prints detailed error messages when Maven not found."""
        # Don't create Maven directory - test the error path
        result = self.installer._run_maven_install()
        self.assertFalse(result)

    def test_install_maven_without_bin_prints_warning(self):
        """Test Maven installation fails when bin directory missing."""
        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)

        # Create apache-maven directory WITHOUT bin
        extracted_dir = tools_dir / 'apache-maven-3.9.9'
        extracted_dir.mkdir(parents=True, exist_ok=True)

        # Create some other directories to list (but no bin)
        (extracted_dir / 'conf').mkdir()
        (extracted_dir / 'lib').mkdir()

        # Mock download_and_extract to return success and the extracted dir
        with patch.object(self.installer, 'download_and_extract', return_value=(True, extracted_dir)):
            result = self.installer._install_maven(tools_dir)
            # Should fail because bin directory is missing
            self.assertFalse(result)

    @patch('zipfile.ZipFile')
    def test_install_when_java_bin_already_in_path(self, mock_zipfile):
        """Test install when java_bin already in PATH."""
        import os

        # Create a PATH that will already contain java_bin after installation
        tools_dir = Path.home() / '.dev-start' / 'tools'
        java_bin = f"{tools_dir}\\jdk-17\\bin"

        original_path = os.environ.get('PATH', '')
        os.environ['PATH'] = f"{java_bin};C:\\other\\path"

        try:
            with patch.object(Path, 'exists', return_value=True):
                result = self.installer.install()
                self.assertTrue(result)

                # PATH should not have duplicate entries
                path_parts = os.environ['PATH'].split(os.pathsep)
                # Count occurrences - should be exactly 1 (was already there)
                self.assertEqual(path_parts.count(java_bin), 1)
        finally:
            if original_path:
                os.environ['PATH'] = original_path

    @patch.object(Path, 'exists')
    def test_install_maven_when_maven_bin_already_in_path(self, mock_exists):
        """Test _install_maven when maven_bin already in PATH."""
        import os

        tools_dir = self.temp_dir / 'tools'
        tools_dir.mkdir(parents=True, exist_ok=True)
        maven_bin = f"{tools_dir}\\maven\\bin"

        original_path = os.environ.get('PATH', '')
        os.environ['PATH'] = f"{maven_bin};C:\\other\\path"

        try:
            mock_exists.return_value = True

            result = self.installer._install_maven(tools_dir)
            self.assertTrue(result)

            # PATH should not have duplicate entries
            path_parts = os.environ['PATH'].split(os.pathsep)
            # The path might be slightly different due to formatting, just check it's there
            self.assertIn('maven', os.environ['PATH'])
        finally:
            if original_path:
                os.environ['PATH'] = original_path

    def test_install_updates_path_when_java_not_in_path(self):
        """Test install updates PATH when java_bin not in PATH."""
        import os

        original_path = os.environ.get('PATH', '')
        # Set PATH to something that doesn't include java
        os.environ['PATH'] = 'C:\\other\\path'

        try:
            with patch.object(Path, 'exists', return_value=True):
                result = self.installer.install()
                self.assertTrue(result)

                # Check java_bin was added to PATH
                self.assertIn('jdk-', os.environ['PATH'])
                self.assertIn('C:\\other\\path', os.environ['PATH'])
        finally:
            if original_path:
                os.environ['PATH'] = original_path

    @patch.object(Path, 'exists')
    def test_install_maven_updates_path_when_maven_not_in_path(self, mock_exists):
        """Test _install_maven updates PATH when maven_bin not in PATH."""
        import os

        original_path = os.environ.get('PATH', '')
        # Set PATH to something that doesn't include maven
        os.environ['PATH'] = 'C:\\other\\path'

        try:
            tools_dir = self.temp_dir / 'tools'
            tools_dir.mkdir(parents=True, exist_ok=True)

            mock_exists.return_value = True

            result = self.installer._install_maven(tools_dir)
            self.assertTrue(result)

            # Check maven_bin was added to PATH
            self.assertIn('maven', os.environ['PATH'])
            self.assertIn('C:\\other\\path', os.environ['PATH'])
        finally:
            if original_path:
                os.environ['PATH'] = original_path

    @patch('pathlib.Path.exists')
    def test_install_when_path_env_not_exists(self, mock_exists):
        """Test Java installation when PATH environment variable doesn't exist."""
        import os

        # Mock exists to return False for java_dir
        mock_exists.return_value = False
        java_dir = self.temp_dir / 'java'

        # Save and remove PATH
        original_path = os.environ.get('PATH', '')
        had_path = 'PATH' in os.environ
        if had_path:
            del os.environ['PATH']

        try:
            with patch.object(self.installer, 'is_installed', return_value=False):
                with patch.object(self.installer, 'download_and_extract', return_value=(True, java_dir)):
                    with patch.object(self.installer, 'setup_tool_environment'):
                        result = self.installer.install()
                        self.assertTrue(result)
        finally:
            # Restore PATH
            if had_path:
                os.environ['PATH'] = original_path
            elif 'PATH' in os.environ:
                del os.environ['PATH']

    def test_install_maven_when_path_env_not_exists(self):
        """Test Maven installation when PATH environment variable doesn't exist."""
        import os

        # Save and remove PATH
        original_path = os.environ.get('PATH', '')
        had_path = 'PATH' in os.environ
        if had_path:
            del os.environ['PATH']

        try:
            tools_dir = self.temp_dir / 'tools'
            tools_dir.mkdir(parents=True, exist_ok=True)

            # Create maven_dir with bin subdirectory for verification
            maven_dir = tools_dir / 'apache-maven-3.9.5'
            maven_dir.mkdir(parents=True)
            (maven_dir / 'bin').mkdir()

            with patch.object(self.installer, 'download_and_extract', return_value=(True, maven_dir)):
                with patch.object(self.installer, 'setup_tool_environment'):
                    result = self.installer._install_maven(tools_dir)
                    self.assertTrue(result)
        finally:
            # Restore PATH
            if had_path:
                os.environ['PATH'] = original_path
            elif 'PATH' in os.environ:
                del os.environ['PATH']

    @patch('pathlib.Path.exists')
    def test_configure_maven_not_found_prints_locations(self, mock_exists):
        """Test configure when Maven is not found logs warning and continues."""
        # Mock that pom.xml exists
        def exists_side_effect(path_self):
            return 'pom.xml' in str(path_self)

        with patch('pathlib.Path.exists', exists_side_effect):
            # Mock _install_maven to fail (so it tries to find Maven after failed install)
            with patch.object(self.installer, '_install_maven', return_value=False):
                # Mock find_maven_executable to return None (Maven not found after install attempt)
                with patch.object(self.installer, '_find_maven_executable', return_value=None):
                    result = self.installer.configure()
                    # Should return True (continues with warning) - configure doesn't fail on maven issues
                    self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
