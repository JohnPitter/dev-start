"""Tests for technology detector."""
import unittest
from pathlib import Path
import tempfile
import shutil
from src.detector import TechnologyDetector, Technology


class TestTechnologyDetector(unittest.TestCase):
    """Test cases for TechnologyDetector."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = TechnologyDetector()
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_detect_java_springboot_with_pom(self):
        """Test detection of Java SpringBoot project with pom.xml."""
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('<project><dependencies><dependency>spring-boot</dependency></dependencies></project>')

        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.JAVA_SPRINGBOOT)

    def test_detect_python_with_requirements(self):
        """Test detection of Python project with requirements.txt."""
        req_file = self.temp_dir / 'requirements.txt'
        req_file.write_text('flask==2.0.0\nrequests==2.26.0')

        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.PYTHON)

    def test_detect_nodejs_with_package_json(self):
        """Test detection of Node.js project with package.json."""
        pkg_file = self.temp_dir / 'package.json'
        pkg_file.write_text('{"name": "test-app", "version": "1.0.0"}')

        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.NODEJS)

    def test_detect_unknown_technology(self):
        """Test detection when no known technology is found."""
        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.UNKNOWN)

    def test_detect_java_from_build_gradle(self):
        """Test detecting Java from build.gradle."""
        gradle_file = self.temp_dir / 'build.gradle'
        gradle_file.write_text('apply plugin: "org.springframework.boot"\ndependencies { implementation "spring-boot-starter-web" }', encoding='utf-8')

        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.JAVA_SPRINGBOOT)

    def test_detect_python_from_setup_py(self):
        """Test detecting Python from setup.py."""
        setup_file = self.temp_dir / 'setup.py'
        setup_file.write_text('from setuptools import setup\nsetup(name="test")', encoding='utf-8')

        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.PYTHON)

    def test_detect_python_from_pyproject_toml(self):
        """Test detecting Python from pyproject.toml."""
        pyproject_file = self.temp_dir / 'pyproject.toml'
        pyproject_file.write_text('[tool.poetry]\nname = "test"', encoding='utf-8')

        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.PYTHON)

    def test_detect_nodejs_from_yarn_lock(self):
        """Test detecting Node.js from yarn.lock."""
        yarn_lock = self.temp_dir / 'yarn.lock'
        yarn_lock.write_text('# yarn lockfile v1', encoding='utf-8')

        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.NODEJS)

    def test_detect_unknown_repo_not_exists(self):
        """Test detecting unknown when repository doesn't exist."""
        non_existent = self.temp_dir / 'non_existent'
        result = self.detector.detect(non_existent)
        self.assertEqual(result, Technology.UNKNOWN)

    def test_get_root_files(self):
        """Test getting root files from repository."""
        # Create some test files
        (self.temp_dir / 'file1.txt').write_text('test', encoding='utf-8')
        (self.temp_dir / 'file2.py').write_text('test', encoding='utf-8')
        (self.temp_dir / 'subdir').mkdir()

        files = self.detector._get_root_files(self.temp_dir)
        self.assertIn('file1.txt', files)
        self.assertIn('file2.py', files)
        self.assertEqual(len([f for f in files if f == 'subdir']), 0)

    def test_matches_technology_python(self):
        """Test matching Python technology."""
        files = ['requirements.txt', 'main.py']
        result = self.detector._matches_technology(self.temp_dir, files, Technology.PYTHON)
        self.assertTrue(result)

    def test_matches_technology_no_match(self):
        """Test not matching any technology."""
        files = ['random.txt', 'other.md']
        result = self.detector._matches_technology(self.temp_dir, files, Technology.PYTHON)
        self.assertFalse(result)

    def test_check_indicators_spring_boot(self):
        """Test checking Spring Boot indicators in file."""
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('spring-boot-starter-web', encoding='utf-8')

        result = self.detector._check_indicators(pom_file, ['spring-boot'])
        self.assertTrue(result)

    def test_check_indicators_not_found(self):
        """Test checking indicators when not found."""
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('<project></project>', encoding='utf-8')

        result = self.detector._check_indicators(pom_file, ['spring-boot'])
        self.assertFalse(result)

    def test_check_indicators_file_not_exists(self):
        """Test checking indicators when file doesn't exist."""
        non_existent = self.temp_dir / 'non_existent.xml'
        result = self.detector._check_indicators(non_existent, ['spring-boot'])
        self.assertFalse(result)

    def test_priority_java_over_others(self):
        """Test that Java/SpringBoot has priority when multiple files exist."""
        # Create files for both Java and Python
        (self.temp_dir / 'pom.xml').write_text(
            '<project><dependencies>spring-boot</dependencies></project>',
            encoding='utf-8'
        )
        (self.temp_dir / 'requirements.txt').write_text('flask', encoding='utf-8')

        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.JAVA_SPRINGBOOT)

    def test_priority_python_over_nodejs(self):
        """Test that Python has priority over Node.js when both exist."""
        # Create files for both Python and Node.js
        (self.temp_dir / 'requirements.txt').write_text('flask', encoding='utf-8')
        (self.temp_dir / 'package.json').write_text('{"name": "test"}', encoding='utf-8')

        result = self.detector.detect(self.temp_dir)
        self.assertEqual(result, Technology.PYTHON)

    def test_get_root_files_with_exception(self):
        """Test getting root files when an exception occurs."""
        from unittest.mock import MagicMock, patch

        # Mock a path that throws an exception when iterdir() is called
        mock_path = MagicMock()
        mock_path.iterdir.side_effect = PermissionError("Access denied")

        files = self.detector._get_root_files(mock_path)
        self.assertEqual(files, [])

    def test_matches_technology_with_invalid_tech(self):
        """Test matching technology with invalid/unknown technology type."""
        # Create a mock technology that doesn't exist in DETECTION_PATTERNS
        class FakeTechnology:
            pass

        fake_tech = FakeTechnology()
        files = ['requirements.txt']

        result = self.detector._matches_technology(self.temp_dir, files, fake_tech)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
