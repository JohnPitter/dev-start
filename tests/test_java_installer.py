"""Tests for Java installer."""
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

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
        """Test finding Maven executable (mvn.cmd)."""
        # Mock to return True for mvn.cmd path
        mock_exists.return_value = True
        result = self.installer._find_maven_executable()
        self.assertIsNotNone(result)
        self.assertIn('mvn.cmd', result)

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
            mock_run.return_value = Mock(returncode=0, stderr='')

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


if __name__ == '__main__':
    unittest.main()
