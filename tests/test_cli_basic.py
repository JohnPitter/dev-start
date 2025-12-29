"""Basic tests for CLI module."""
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import shutil

from src.cli import DevStartCLI


class TestCLIBasic(unittest.TestCase):
    """Test CLI basic functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cli = DevStartCLI()

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_cli_initialization(self):
        """Test CLI initializes correctly."""
        self.assertIsNotNone(self.cli.proxy_manager)
        self.assertIsNotNone(self.cli.repo_manager)
        self.assertIsNotNone(self.cli.detector)
        self.assertTrue(self.cli.base_dir.exists())

    def test_setup_proxy_http(self):
        """Test setting up HTTP proxy."""
        self.cli.setup_proxy(http_proxy='http://proxy:8080')
        self.assertEqual(self.cli.proxy_manager.http_proxy, 'http://proxy:8080')

    def test_setup_proxy_https(self):
        """Test setting up HTTPS proxy."""
        self.cli.setup_proxy(https_proxy='https://proxy:8080')
        self.assertEqual(self.cli.proxy_manager.https_proxy, 'https://proxy:8080')

    def test_setup_proxy_both(self):
        """Test setting up both HTTP and HTTPS proxy."""
        self.cli.setup_proxy(http_proxy='http://proxy:8080', https_proxy='https://proxy:8080')
        self.assertEqual(self.cli.proxy_manager.http_proxy, 'http://proxy:8080')
        self.assertEqual(self.cli.proxy_manager.https_proxy, 'https://proxy:8080')

    def test_remove_readonly(self):
        """Test readonly file handler."""
        # Create a test file
        test_file = self.temp_dir / 'test.txt'
        test_file.write_text('test content', encoding='utf-8')
        test_path = str(test_file)

        # Create a test function
        mock_func = Mock()

        # Call remove_readonly
        self.cli.remove_readonly(mock_func, test_path, None)

        # Verify function was called
        mock_func.assert_called_once_with(test_path)

    @patch('subprocess.run')
    def test_ensure_git_installed_already_installed(self, mock_run):
        """Test Git check when already installed."""
        mock_run.return_value = Mock(returncode=0, stdout='git version 2.40.0')
        result = self.cli.ensure_git_installed()
        self.assertTrue(result)

    def test_safe_rmtree_success(self):
        """Test safe directory removal success."""
        test_dir = self.temp_dir / 'test_removal'
        test_dir.mkdir()
        (test_dir / 'file.txt').write_text('test', encoding='utf-8')

        result = self.cli.safe_rmtree(str(test_dir))
        self.assertTrue(result)
        self.assertFalse(test_dir.exists())

    def test_safe_rmtree_nonexistent(self):
        """Test safe directory removal when directory doesn't exist."""
        non_existent = str(self.temp_dir / 'non_existent')
        result = self.cli.safe_rmtree(non_existent)
        # Returns False because directory doesn't exist (nothing to remove)
        self.assertFalse(result)

    @patch('shutil.rmtree')
    @patch('os.path.exists')
    def test_safe_rmtree_permission_error(self, mock_exists, mock_rmtree):
        """Test safe directory removal with permission error."""
        mock_exists.return_value = True
        mock_rmtree.side_effect = PermissionError("Access denied")

        result = self.cli.safe_rmtree(str(self.temp_dir))
        self.assertFalse(result)

    @patch('shutil.rmtree')
    @patch('os.path.exists')
    def test_safe_rmtree_general_exception(self, mock_exists, mock_rmtree):
        """Test safe directory removal with general exception."""
        mock_exists.return_value = True
        mock_rmtree.side_effect = Exception("Unknown error")

        result = self.cli.safe_rmtree(str(self.temp_dir))
        self.assertFalse(result)

    @patch('click.confirm')
    @patch('click.prompt')
    def test_configure_git(self, mock_prompt, mock_confirm):
        """Test Git configuration."""
        mock_confirm.side_effect = [True, True]  # Confirm config and SSL
        mock_prompt.side_effect = ['John Doe', 'john@example.com']

        with patch.object(self.cli, 'git_installer') as mock_git:
            mock_git.configure.return_value = True
            self.cli._configure_git()
            mock_git.configure.assert_called_once()

    @patch('click.confirm')
    def test_configure_git_declined(self, mock_confirm):
        """Test Git configuration when user declines."""
        mock_confirm.return_value = False

        with patch.object(self.cli, 'git_installer') as mock_git:
            self.cli._configure_git()
            mock_git.configure.assert_not_called()

    @patch('click.confirm')
    @patch('click.prompt')
    def test_configure_git_failure(self, mock_prompt, mock_confirm):
        """Test Git configuration with failure."""
        mock_confirm.side_effect = [True, True]
        mock_prompt.side_effect = ['John Doe', 'john@example.com']

        with patch.object(self.cli, 'git_installer') as mock_git:
            mock_git.configure.return_value = False
            self.cli._configure_git()
            mock_git.configure.assert_called_once()

    @patch('subprocess.run')
    @patch('click.confirm')
    def test_ensure_git_not_installed_decline(self, mock_confirm, mock_run):
        """Test Git installation when user declines."""
        mock_run.side_effect = FileNotFoundError()
        mock_confirm.return_value = False

        result = self.cli.ensure_git_installed()
        self.assertFalse(result)

    @patch('subprocess.run')
    @patch('click.confirm')
    @patch('click.prompt')
    def test_ensure_git_install_success(self, mock_prompt, mock_confirm, mock_run):
        """Test Git installation success."""
        mock_run.side_effect = [
            FileNotFoundError(),  # is_installed check
            Mock(returncode=1),    # _is_git_configured check
            Mock(returncode=1),    # _is_git_configured check
            Mock(returncode=0),    # set name
            Mock(returncode=0),    # set email
            Mock(returncode=0),    # set ssl
        ]
        mock_confirm.side_effect = [True, True, True]  # Install, configure, SSL
        mock_prompt.side_effect = ['John Doe', 'john@example.com']

        with patch.object(self.cli, 'git_installer') as mock_git:
            mock_git.is_installed.return_value = False
            mock_git.install.return_value = True
            mock_git.configure.return_value = True
            result = self.cli.ensure_git_installed()
            self.assertTrue(result)

    @patch('subprocess.run')
    def test_ensure_git_not_configured(self, mock_run):
        """Test Git installed but not configured."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout='git version 2.40.0'),  # is_installed
            Mock(returncode=0, stdout='2.40.0'),               # detect_version
            Mock(returncode=1),                                 # _is_git_configured (name)
            Mock(returncode=1),                                 # _is_git_configured (email)
        ]

        with patch.object(self.cli, '_configure_git') as mock_config:
            result = self.cli.ensure_git_installed()
            self.assertTrue(result)
            mock_config.assert_called_once()

    def test_process_repository_git_not_installed(self):
        """Test processing repository when Git not installed."""
        with patch.object(self.cli, 'ensure_git_installed', return_value=False):
            result = self.cli.process_repository('https://github.com/user/repo')
            self.assertFalse(result)

    def test_process_repository_clone_fails(self):
        """Test processing repository when clone fails."""
        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            with patch.object(self.cli, 'safe_rmtree', return_value=True):
                with patch.object(self.cli.repo_manager, 'clone_repository', return_value=False):
                    result = self.cli.process_repository('https://github.com/user/repo')
                    self.assertFalse(result)

    def test_get_installer_java(self):
        """Test getting Java installer."""
        from src.detector import Technology
        installer = self.cli._get_installer(Technology.JAVA_SPRINGBOOT, self.temp_dir)
        self.assertIsNotNone(installer)

    def test_get_installer_nodejs(self):
        """Test getting Node.js installer."""
        from src.detector import Technology
        installer = self.cli._get_installer(Technology.NODEJS, self.temp_dir)
        self.assertIsNotNone(installer)

    def test_get_installer_python(self):
        """Test getting Python installer."""
        from src.detector import Technology
        installer = self.cli._get_installer(Technology.PYTHON, self.temp_dir)
        self.assertIsNotNone(installer)

    def test_get_installer_unknown(self):
        """Test getting installer for unknown technology."""
        from src.detector import Technology
        installer = self.cli._get_installer(Technology.UNKNOWN, self.temp_dir)
        self.assertIsNone(installer)

    @patch('click.confirm')
    def test_process_repository_existing_overwrite_yes(self, mock_confirm):
        """Test processing repository when existing and user confirms overwrite."""
        mock_confirm.return_value = True  # User confirms overwrite

        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            # Mock Path.exists to return True (repo exists)
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(self.cli, 'safe_rmtree', return_value=True):
                    with patch.object(self.cli.repo_manager, 'clone_repository', return_value=False):
                        result = self.cli.process_repository('https://github.com/user/test_repo')
                        self.assertFalse(result)

    @patch('click.confirm')
    def test_process_repository_existing_overwrite_no(self, mock_confirm):
        """Test processing repository when existing and user declines overwrite."""
        mock_confirm.return_value = False  # User declines overwrite

        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            # Mock Path.exists to return True (repo exists)
            with patch('pathlib.Path.exists', return_value=True):
                result = self.cli.process_repository('https://github.com/user/test_repo')
                self.assertFalse(result)

    @patch('click.confirm')
    def test_process_repository_existing_remove_fails(self, mock_confirm):
        """Test processing repository when removal of existing repo fails."""
        mock_confirm.return_value = True  # User confirms overwrite

        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            # Mock Path.exists to return True (repo exists)
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(self.cli, 'safe_rmtree', return_value=False):
                    result = self.cli.process_repository('https://github.com/user/test_repo')
                    self.assertFalse(result)

    def test_process_repository_unknown_technology(self):
        """Test processing repository when technology cannot be detected."""
        from src.detector import Technology

        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            with patch.object(self.cli, 'safe_rmtree', return_value=True):
                with patch.object(self.cli.repo_manager, 'clone_repository', return_value=True):
                    with patch.object(self.cli.detector, 'detect', return_value=Technology.UNKNOWN):
                        result = self.cli.process_repository('https://github.com/user/repo')
                        self.assertFalse(result)

    def test_process_repository_no_installer(self):
        """Test processing repository when no installer is available."""
        from src.detector import Technology

        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            with patch.object(self.cli, 'safe_rmtree', return_value=True):
                with patch.object(self.cli.repo_manager, 'clone_repository', return_value=True):
                    with patch.object(self.cli.detector, 'detect', return_value=Technology.PYTHON):
                        with patch.object(self.cli, '_get_installer', return_value=None):
                            result = self.cli.process_repository('https://github.com/user/repo')
                            self.assertFalse(result)

    def test_process_repository_installation_fails(self):
        """Test processing repository when technology installation fails."""
        from src.detector import Technology

        mock_installer = Mock()
        mock_installer.is_installed.return_value = False
        mock_installer.install.return_value = False

        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            with patch.object(self.cli, 'safe_rmtree', return_value=True):
                with patch.object(self.cli.repo_manager, 'clone_repository', return_value=True):
                    with patch.object(self.cli.detector, 'detect', return_value=Technology.PYTHON):
                        with patch.object(self.cli, '_get_installer', return_value=mock_installer):
                            result = self.cli.process_repository('https://github.com/user/repo')
                            self.assertFalse(result)

    def test_process_repository_configuration_fails(self):
        """Test processing repository when configuration fails."""
        from src.detector import Technology

        mock_installer = Mock()
        mock_installer.is_installed.return_value = True
        mock_installer.configure.return_value = False

        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            with patch.object(self.cli, 'safe_rmtree', return_value=True):
                with patch.object(self.cli.repo_manager, 'clone_repository', return_value=True):
                    with patch.object(self.cli.detector, 'detect', return_value=Technology.PYTHON):
                        with patch.object(self.cli, '_get_installer', return_value=mock_installer):
                            result = self.cli.process_repository('https://github.com/user/repo')
                            self.assertFalse(result)

    def test_process_repository_success(self):
        """Test successful repository processing."""
        from src.detector import Technology

        mock_installer = Mock()
        mock_installer.is_installed.return_value = True
        mock_installer.configure.return_value = True

        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            with patch.object(self.cli, 'safe_rmtree', return_value=True):
                with patch.object(self.cli.repo_manager, 'clone_repository', return_value=True):
                    with patch.object(self.cli.detector, 'detect', return_value=Technology.PYTHON):
                        with patch.object(self.cli, '_get_installer', return_value=mock_installer):
                            result = self.cli.process_repository('https://github.com/user/repo')
                            self.assertTrue(result)

    def test_process_repository_install_and_configure(self):
        """Test repository processing with installation and configuration."""
        from src.detector import Technology

        mock_installer = Mock()
        mock_installer.is_installed.return_value = False
        mock_installer.install.return_value = True
        mock_installer.configure.return_value = True

        with patch.object(self.cli, 'ensure_git_installed', return_value=True):
            with patch.object(self.cli, 'safe_rmtree', return_value=True):
                with patch.object(self.cli.repo_manager, 'clone_repository', return_value=True):
                    with patch.object(self.cli.detector, 'detect', return_value=Technology.NODEJS):
                        with patch.object(self.cli, '_get_installer', return_value=mock_installer):
                            result = self.cli.process_repository('https://github.com/user/repo')
                            self.assertTrue(result)
                            mock_installer.install.assert_called_once()
                            mock_installer.configure.assert_called_once()


if __name__ == '__main__':
    unittest.main()
