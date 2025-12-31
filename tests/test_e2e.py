"""End-to-end tests with real repositories."""
import pytest
import unittest
import tempfile
import shutil
import subprocess
from pathlib import Path
from src.proxy_manager import ProxyManager
from src.repo_manager import RepositoryManager
from src.detector import TechnologyDetector, Technology
from src.env_manager import EnvironmentManager


def is_git_available():
    """Check if git is available and can access the network."""
    try:
        result = subprocess.run(
            ['git', 'ls-remote', 'https://github.com/octocat/Hello-World.git', 'HEAD'],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


@pytest.mark.e2e
@unittest.skipUnless(is_git_available(), "Git or network not available")
class TestE2ERealRepositories(unittest.TestCase):
    """E2E tests with real public repositories."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures."""
        cls.temp_base = Path(tempfile.mkdtemp(prefix='dev-start-e2e-'))
        cls.proxy_manager = ProxyManager()
        cls.repo_manager = RepositoryManager(cls.proxy_manager)
        cls.detector = TechnologyDetector()

    @classmethod
    def tearDownClass(cls):
        """Clean up class-level fixtures."""
        if cls.temp_base.exists():
            shutil.rmtree(cls.temp_base)

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = self.temp_base / f'test_{id(self)}'
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    @pytest.mark.e2e
    def test_clone_python_flask_hello_world(self):
        """Test cloning a simple Python Flask repository."""
        # Small public Flask hello world repository
        repo_url = 'https://github.com/miguelgrinberg/flask-celery-example.git'
        repo_path = self.test_dir / 'flask-celery-example'

        # Clone
        result = self.repo_manager.clone_repository(repo_url, repo_path)
        self.assertTrue(result, "Repository should be cloned successfully")
        self.assertTrue(repo_path.exists(), "Repository directory should exist")

        # Verify it's a Git repository
        git_dir = repo_path / '.git'
        self.assertTrue(git_dir.exists(), "Should have .git directory")

        # Detect technology
        technology = self.detector.detect(repo_path)
        self.assertEqual(
            technology,
            Technology.PYTHON,
            "Should detect Python technology"
        )

        # Verify requirements.txt exists
        requirements = repo_path / 'requirements.txt'
        self.assertTrue(requirements.exists(), "Should have requirements.txt")

    @pytest.mark.e2e
    def test_clone_nodejs_simple_app(self):
        """Test cloning a simple Node.js repository."""
        # Small public Node.js example
        repo_url = 'https://github.com/kentcdodds/calculator.git'
        repo_path = self.test_dir / 'calculator'

        # Clone
        result = self.repo_manager.clone_repository(repo_url, repo_path)
        self.assertTrue(result, "Repository should be cloned successfully")

        # Detect technology
        technology = self.detector.detect(repo_path)
        self.assertEqual(
            technology,
            Technology.NODEJS,
            "Should detect Node.js technology"
        )

        # Verify package.json exists
        package_json = repo_path / 'package.json'
        self.assertTrue(package_json.exists(), "Should have package.json")

    @pytest.mark.e2e
    def test_environment_setup_python_project(self):
        """Test complete environment setup for Python project."""
        # Clone a small Python project
        repo_url = 'https://github.com/pallets/click.git'
        repo_path = self.test_dir / 'click'

        # Clone
        result = self.repo_manager.clone_repository(repo_url, repo_path)
        self.assertTrue(result)

        # Detect
        technology = self.detector.detect(repo_path)
        self.assertEqual(technology, Technology.PYTHON)

        # Setup environment
        env_manager = EnvironmentManager(repo_path)
        env_manager.create_env_file({
            'PYTHONPATH': str(repo_path),
            'ENV': 'development'
        })

        # Verify .env created
        env_file = repo_path / '.env'
        self.assertTrue(env_file.exists())

        content = env_file.read_text()
        self.assertIn('PYTHONPATH', content)
        self.assertIn('development', content)

    @pytest.mark.e2e
    def test_detect_unknown_repository(self):
        """Test detection of repository with unknown technology."""
        # Clone a repository without standard project files
        repo_url = 'https://github.com/github/gitignore.git'
        repo_path = self.test_dir / 'gitignore'

        # Clone
        result = self.repo_manager.clone_repository(repo_url, repo_path)
        self.assertTrue(result)

        # Detect - should be UNKNOWN
        technology = self.detector.detect(repo_path)
        self.assertEqual(
            technology,
            Technology.UNKNOWN,
            "Should detect as UNKNOWN for non-project repository"
        )

    @pytest.mark.e2e
    def test_repository_name_extraction(self):
        """Test extracting repository name from various URL formats."""
        test_cases = [
            ('https://github.com/user/repo.git', 'repo'),
            ('https://github.com/user/my-project', 'my-project'),
            ('https://gitlab.com/org/project.git', 'project'),
        ]

        for url, expected_name in test_cases:
            name = self.repo_manager.get_repo_name(url)
            self.assertEqual(
                name,
                expected_name,
                f"Should extract '{expected_name}' from '{url}'"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'e2e'])
