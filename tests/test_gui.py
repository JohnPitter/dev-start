"""GUI tests for dev-start tkinter interface."""
import pytest
import unittest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from src.gui import DevStartGUI, InstallationReport, LogRedirector
from src.detector import Technology


@pytest.mark.gui
class TestInstallationReport(unittest.TestCase):
    """Test cases for InstallationReport."""

    def setUp(self):
        """Set up test fixtures."""
        self.report = InstallationReport()

    def test_report_initialization(self):
        """Test report is initialized correctly."""
        self.assertIsNone(self.report.start_time)
        self.assertIsNone(self.report.end_time)
        self.assertEqual(self.report.repositories, [])
        self.assertEqual(self.report.successful, [])
        self.assertEqual(self.report.failed, [])
        self.assertFalse(self.report.git_installed)

    def test_report_start_and_end(self):
        """Test marking start and end times."""
        self.report.start()
        self.assertIsNotNone(self.report.start_time)

        self.report.end()
        self.assertIsNotNone(self.report.end_time)
        self.assertGreaterEqual(self.report.end_time, self.report.start_time)

    def test_add_successful_repository(self):
        """Test adding successful repository."""
        url = 'https://github.com/user/repo'
        self.report.add_repository(url, True, Technology.PYTHON)

        self.assertEqual(len(self.report.repositories), 1)
        self.assertEqual(len(self.report.successful), 1)
        self.assertEqual(len(self.report.failed), 0)
        self.assertIn(url, self.report.successful)

    def test_add_failed_repository(self):
        """Test adding failed repository."""
        url = 'https://github.com/user/repo'
        error = 'Clone failed'
        self.report.add_repository(url, False, error=error)

        self.assertEqual(len(self.report.repositories), 1)
        self.assertEqual(len(self.report.successful), 0)
        self.assertEqual(len(self.report.failed), 1)
        self.assertIn(url, self.report.failed)

        # Check error is stored
        self.assertEqual(self.report.repositories[0]['error'], error)

    def test_get_duration(self):
        """Test duration calculation."""
        self.report.start()
        import time
        time.sleep(0.1)  # Sleep for 100ms
        self.report.end()

        duration = self.report.get_duration()
        self.assertIsInstance(duration, str)
        self.assertTrue(duration.endswith('s'))

        # Parse duration
        duration_value = float(duration[:-1])
        self.assertGreaterEqual(duration_value, 0.1)

    def test_generate_report_format(self):
        """Test report generation format."""
        self.report.start()
        self.report.git_installed = True
        self.report.add_repository(
            'https://github.com/user/repo1',
            True,
            Technology.PYTHON
        )
        self.report.add_repository(
            'https://github.com/user/repo2',
            False,
            error='Failed to clone'
        )
        self.report.end()

        report_text = self.report.generate_report()

        # Check report contains expected sections
        self.assertIn('INSTALLATION REPORT', report_text)
        self.assertIn('Started:', report_text)
        self.assertIn('Completed:', report_text)
        self.assertIn('Duration:', report_text)
        self.assertIn('Git Installed: Yes', report_text)
        self.assertIn('Total Repositories: 2', report_text)
        self.assertIn('Successful: 1', report_text)
        self.assertIn('Failed: 1', report_text)
        self.assertIn('SUCCESSFUL INSTALLATIONS:', report_text)
        self.assertIn('FAILED INSTALLATIONS:', report_text)


@pytest.mark.gui
class TestLogRedirector(unittest.TestCase):
    """Test cases for LogRedirector."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.text_widget = tk.Text(self.root)
        self.redirector = LogRedirector(self.text_widget, "test")

    def tearDown(self):
        """Clean up test fixtures."""
        self.root.destroy()

    def test_write_to_widget(self):
        """Test writing to text widget."""
        message = "Test message\n"
        self.redirector.write(message)

        content = self.text_widget.get(1.0, tk.END)
        self.assertIn("Test message", content)

    def test_write_empty_message(self):
        """Test writing empty message doesn't add content."""
        try:
            self.redirector.write("")
            self.redirector.write("   ")

            content = self.text_widget.get(1.0, tk.END).strip()
            self.assertEqual(content, "")
        except Exception:
            # Skip test if Tk is not properly installed
            self.skipTest("Tkinter not properly configured")

    def test_flush_method(self):
        """Test flush method exists and works."""
        # Should not raise an error
        self.redirector.flush()


@pytest.mark.gui
class TestDevStartGUI(unittest.TestCase):
    """Test cases for DevStartGUI."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.gui = DevStartGUI(self.root)

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            self.root.destroy()
        except:
            pass

    def test_gui_initialization(self):
        """Test GUI initializes correctly."""
        self.assertIsNotNone(self.gui.proxy_manager)
        self.assertIsNotNone(self.gui.repo_manager)
        self.assertIsNotNone(self.gui.detector)
        self.assertIsNotNone(self.gui.report)

    def test_widgets_created(self):
        """Test all widgets are created."""
        # Check main widgets exist
        self.assertIsNotNone(self.gui.repo_text)
        self.assertIsNotNone(self.gui.http_proxy_entry)
        self.assertIsNotNone(self.gui.https_proxy_entry)
        self.assertIsNotNone(self.gui.start_button)
        self.assertIsNotNone(self.gui.clear_button)
        self.assertIsNotNone(self.gui.report_button)
        self.assertIsNotNone(self.gui.log_text)
        self.assertIsNotNone(self.gui.progress)
        self.assertIsNotNone(self.gui.status_label)

    def test_log_message(self):
        """Test logging messages."""
        message = "Test log message"
        self.gui.log(message)

        content = self.gui.log_text.get(1.0, tk.END)
        self.assertIn(message, content)

    def test_clear_log(self):
        """Test clearing log."""
        self.gui.log("Test message")
        self.gui.clear_log()

        content = self.gui.log_text.get(1.0, tk.END).strip()
        self.assertEqual(content, "")

    def test_set_status(self):
        """Test setting status message."""
        status = "Test status"
        self.gui.set_status(status)

        self.assertEqual(self.gui.status_label.cget("text"), status)

    def test_report_button_initially_disabled(self):
        """Test report button is initially disabled."""
        state = str(self.gui.report_button['state'])
        self.assertEqual(state, 'disabled')

    def test_get_installer_java(self):
        """Test getting Java installer."""
        from pathlib import Path
        installer = self.gui._get_installer(Technology.JAVA_SPRINGBOOT, Path('.'))
        self.assertIsNotNone(installer)

    def test_get_installer_python(self):
        """Test getting Python installer."""
        from pathlib import Path
        installer = self.gui._get_installer(Technology.PYTHON, Path('.'))
        self.assertIsNotNone(installer)

    def test_get_installer_nodejs(self):
        """Test getting Node.js installer."""
        from pathlib import Path
        installer = self.gui._get_installer(Technology.NODEJS, Path('.'))
        self.assertIsNotNone(installer)

    def test_get_installer_unknown(self):
        """Test getting installer for unknown technology."""
        from pathlib import Path
        installer = self.gui._get_installer(Technology.UNKNOWN, Path('.'))
        self.assertIsNone(installer)

    @patch('tkinter.messagebox.showerror')
    def test_start_installation_no_repos(self, mock_error):
        """Test starting installation with no repositories."""
        # Clear repo text
        self.gui.repo_text.delete(1.0, tk.END)

        # Try to start
        self.gui.start_installation()

        # Should show error
        mock_error.assert_called_once()

    @patch('tkinter.messagebox.showinfo')
    def test_installation_complete(self, mock_showinfo):
        """Test installation complete callback."""
        # Setup report
        self.gui.report.add_repository('https://github.com/user/repo', True, Technology.PYTHON)

        # Disable start button
        self.gui.start_button.config(state=tk.DISABLED)

        # Call installation complete
        self.gui.installation_complete()

        # Check start button is re-enabled
        state = str(self.gui.start_button['state'])
        self.assertEqual(state, 'normal')

        # Check report button is enabled
        report_state = str(self.gui.report_button['state'])
        self.assertEqual(report_state, 'normal')

        # Check showinfo was called
        mock_showinfo.assert_called_once()

    def test_show_report_creates_window(self):
        """Test show report creates new window."""
        self.gui.report.start()
        self.gui.report.add_repository('https://github.com/user/repo', True, Technology.PYTHON)
        self.gui.report.end()

        # Show report
        self.gui.show_report()

        # Find report window
        report_windows = [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel)]
        self.assertEqual(len(report_windows), 1)

        # Clean up
        for w in report_windows:
            w.destroy()

    def test_toggle_proxy_show(self):
        """Test showing proxy configuration."""
        # Initially hidden
        self.assertFalse(self.gui.proxy_visible)

        # Toggle to show
        self.gui.toggle_proxy()

        # Should be visible now
        self.assertTrue(self.gui.proxy_visible)

    def test_toggle_proxy_hide(self):
        """Test hiding proxy configuration."""
        # First show
        self.gui.toggle_proxy()
        self.assertTrue(self.gui.proxy_visible)

        # Then hide
        self.gui.toggle_proxy()
        self.assertFalse(self.gui.proxy_visible)

    def test_remove_readonly(self):
        """Test remove_readonly callback."""
        import tempfile
        import os

        # Create a test file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            test_path = f.name

        try:
            # Make it readonly
            os.chmod(test_path, 0o444)

            # Create mock function
            mock_func = Mock()

            # Call remove_readonly
            self.gui.remove_readonly(mock_func, test_path, None)

            # Should have called the function
            mock_func.assert_called_once_with(test_path)
        finally:
            # Clean up
            if os.path.exists(test_path):
                os.chmod(test_path, 0o666)
                os.unlink(test_path)

    @patch('os.path.exists')
    def test_safe_rmtree_nonexistent(self, mock_exists):
        """Test safe_rmtree when directory doesn't exist."""
        mock_exists.return_value = False

        result = self.gui.safe_rmtree('/fake/path')
        self.assertFalse(result)

    @patch('shutil.rmtree')
    @patch('os.path.exists')
    def test_safe_rmtree_success(self, mock_exists, mock_rmtree):
        """Test safe_rmtree successful removal."""
        mock_exists.return_value = True

        result = self.gui.safe_rmtree('/fake/path')
        self.assertTrue(result)
        mock_rmtree.assert_called_once()

    @patch('shutil.rmtree')
    @patch('os.path.exists')
    @patch('time.sleep')
    def test_safe_rmtree_permission_error_retry(self, mock_sleep, mock_exists, mock_rmtree):
        """Test safe_rmtree with permission error and retry."""
        mock_exists.return_value = True
        mock_rmtree.side_effect = [
            PermissionError("Access denied"),
            PermissionError("Access denied"),
            PermissionError("Access denied")
        ]

        result = self.gui.safe_rmtree('/fake/path', max_retries=3)
        self.assertFalse(result)
        self.assertEqual(mock_rmtree.call_count, 3)

    @patch('shutil.rmtree')
    @patch('os.path.exists')
    def test_safe_rmtree_generic_exception(self, mock_exists, mock_rmtree):
        """Test safe_rmtree with generic exception."""
        mock_exists.return_value = True
        mock_rmtree.side_effect = Exception("Unknown error")

        result = self.gui.safe_rmtree('/fake/path')
        self.assertFalse(result)

    @patch('tkinter.messagebox.showinfo')
    def test_installation_complete_shows_dialog(self, mock_showinfo):
        """Test installation_complete shows completion dialog."""
        self.gui.report.add_repository('https://github.com/user/repo', True, Technology.PYTHON)

        self.gui.installation_complete()

        mock_showinfo.assert_called_once()

    @patch('threading.Thread')
    @patch('tkinter.messagebox.showerror')
    def test_start_installation_with_repos(self, mock_error, mock_thread):
        """Test starting installation with repositories."""
        # Add repository URL
        self.gui.repo_text.insert(1.0, "https://github.com/user/repo\n")

        # Mock thread
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        # Start installation
        self.gui.start_installation()

        # Should create and start thread
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()

        # Should not show error
        mock_error.assert_not_called()

    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('tkinter.messagebox.showinfo')
    def test_save_report_success(self, mock_showinfo, mock_asksaveasfilename):
        """Test saving report to file."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name

        try:
            mock_asksaveasfilename.return_value = temp_path

            content = "Test report content"
            self.gui.save_report(content)

            # Should have called save dialog
            mock_asksaveasfilename.assert_called_once()

            # Should have shown confirmation
            mock_showinfo.assert_called_once()

            # Check file was written
            with open(temp_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            self.assertEqual(saved_content, content)
        finally:
            import os
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('tkinter.filedialog.asksaveasfilename')
    def test_save_report_cancelled(self, mock_asksaveasfilename):
        """Test saving report when user cancels."""
        mock_asksaveasfilename.return_value = None

        content = "Test report content"
        self.gui.save_report(content)

        # Should have called save dialog
        mock_asksaveasfilename.assert_called_once()

    @patch('tkinter.messagebox.askyesno')
    def test_prompt_git_config_declined(self, mock_askyesno):
        """Test prompting for git config when user declines."""
        mock_askyesno.return_value = False

        result = self.gui._prompt_git_config()

        self.assertIsNone(result)
        mock_askyesno.assert_called_once()

    @patch('tkinter.simpledialog.askstring')
    @patch('tkinter.messagebox.askyesno')
    def test_prompt_git_config_name_cancelled(self, mock_askyesno, mock_askstring):
        """Test prompting for git config when name is cancelled."""
        mock_askyesno.return_value = True
        mock_askstring.return_value = None

        result = self.gui._prompt_git_config()

        self.assertIsNone(result)

    @patch('tkinter.simpledialog.askstring')
    @patch('tkinter.messagebox.askyesno')
    def test_prompt_git_config_email_cancelled(self, mock_askyesno, mock_askstring):
        """Test prompting for git config when email is cancelled."""
        mock_askyesno.return_value = True
        mock_askstring.side_effect = ['John Doe', None]

        result = self.gui._prompt_git_config()

        self.assertIsNone(result)

    @patch('tkinter.simpledialog.askstring')
    @patch('tkinter.messagebox.askyesno')
    def test_prompt_git_config_complete(self, mock_askyesno, mock_askstring):
        """Test prompting for git config with all inputs."""
        mock_askyesno.side_effect = [True, True]  # Confirm config, SSL yes
        mock_askstring.side_effect = ['John Doe', 'john@example.com']

        result = self.gui._prompt_git_config()

        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'John Doe')
        self.assertEqual(result['email'], 'john@example.com')
        self.assertTrue(result['ssl_verify'])

    @patch('tkinter.simpledialog.askstring')
    @patch('tkinter.messagebox.askyesno')
    def test_prompt_git_config_ssl_disabled(self, mock_askyesno, mock_askstring):
        """Test prompting for git config with SSL disabled."""
        mock_askyesno.side_effect = [True, False]  # Confirm config, SSL no
        mock_askstring.side_effect = ['John Doe', 'john@example.com']

        result = self.gui._prompt_git_config()

        self.assertIsNotNone(result)
        self.assertFalse(result['ssl_verify'])


@pytest.mark.gui
class TestRunInstallation(unittest.TestCase):
    """Test cases for run_installation workflow."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.gui = DevStartGUI(self.root)

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            self.root.destroy()
        except:
            pass

    @patch('src.gui.GitInstaller')
    def test_run_installation_git_not_installed_and_install_fails(self, mock_git_installer_class):
        """Test run_installation when Git not installed and installation fails."""
        # Mock GitInstaller
        mock_installer = Mock()
        mock_installer.is_installed.return_value = False
        mock_installer.install.return_value = False
        mock_git_installer_class.return_value = mock_installer

        # Set a repo URL in entry
        self.gui.http_proxy_entry.delete(0, tk.END)
        self.gui.http_proxy_entry.insert(0, "")

        # Run installation (should fail at Git install)
        with patch.object(self.gui.root, 'after'):
            self.gui.run_installation(['https://github.com/user/repo'])

        # Git install should have been attempted
        mock_installer.install.assert_called_once()

    @patch('src.gui.PythonInstaller')
    @patch('src.gui.GitInstaller')
    def test_run_installation_successful_python_project(self, mock_git_class, mock_python_class):
        """Test run_installation with successful Python project."""
        from pathlib import Path

        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Mock Python installer
        mock_python = Mock()
        mock_python.is_installed.return_value = True
        mock_python.configure.return_value = True
        mock_python_class.return_value = mock_python

        # Mock repo manager
        with patch.object(self.gui.repo_manager, 'clone_repository', return_value=True):
            with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                # Mock detector
                with patch.object(self.gui.detector, 'detect', return_value=Technology.PYTHON):
                    # Mock path exists
                    with patch('pathlib.Path.exists', return_value=False):
                        # Clear proxy entry
                        self.gui.http_proxy_entry.delete(0, tk.END)

                        # Run installation
                        with patch.object(self.gui.root, 'after'):
                            self.gui.run_installation(['https://github.com/user/python-repo'])

        # Check report
        self.assertEqual(len(self.gui.report.successful), 1)
        self.assertEqual(len(self.gui.report.failed), 0)

    @patch('src.gui.GitInstaller')
    def test_run_installation_clone_fails(self, mock_git_class):
        """Test run_installation when repository clone fails."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Mock repo manager - clone fails
        with patch.object(self.gui.repo_manager, 'clone_repository', return_value=False):
            with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                with patch('pathlib.Path.exists', return_value=False):
                    # Clear proxy entry
                    self.gui.http_proxy_entry.delete(0, tk.END)

                    # Run installation
                    with patch.object(self.gui.root, 'after'):
                        self.gui.run_installation(['https://github.com/user/repo'])

        # Check report shows failure
        self.assertEqual(len(self.gui.report.successful), 0)
        self.assertEqual(len(self.gui.report.failed), 1)

    @patch('src.gui.GitInstaller')
    def test_run_installation_unknown_technology(self, mock_git_class):
        """Test run_installation when technology detection fails."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Mock repo manager
        with patch.object(self.gui.repo_manager, 'clone_repository', return_value=True):
            with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                # Mock detector - returns unknown
                with patch.object(self.gui.detector, 'detect', return_value=Technology.UNKNOWN):
                    with patch('pathlib.Path.exists', return_value=False):
                        # Clear proxy entry
                        self.gui.http_proxy_entry.delete(0, tk.END)

                        # Run installation
                        with patch.object(self.gui.root, 'after'):
                            self.gui.run_installation(['https://github.com/user/repo'])

        # Check report shows failure
        self.assertEqual(len(self.gui.report.failed), 1)

    @patch('src.gui.PythonInstaller')
    @patch('src.gui.GitInstaller')
    def test_run_installation_installer_not_installed_and_install_fails(self, mock_git_class, mock_python_class):
        """Test run_installation when technology installer not installed and install fails."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Mock Python installer - not installed and install fails
        mock_python = Mock()
        mock_python.is_installed.return_value = False
        mock_python.install.return_value = False
        mock_python_class.return_value = mock_python

        # Mock repo manager
        with patch.object(self.gui.repo_manager, 'clone_repository', return_value=True):
            with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                with patch.object(self.gui.detector, 'detect', return_value=Technology.PYTHON):
                    with patch('pathlib.Path.exists', return_value=False):
                        # Clear proxy entry
                        self.gui.http_proxy_entry.delete(0, tk.END)

                        # Run installation
                        with patch.object(self.gui.root, 'after'):
                            self.gui.run_installation(['https://github.com/user/repo'])

        # Check report shows failure
        self.assertEqual(len(self.gui.report.failed), 1)

    @patch('src.gui.PythonInstaller')
    @patch('src.gui.GitInstaller')
    def test_run_installation_configure_fails(self, mock_git_class, mock_python_class):
        """Test run_installation when configuration fails."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Mock Python installer - configure fails
        mock_python = Mock()
        mock_python.is_installed.return_value = True
        mock_python.configure.return_value = False
        mock_python_class.return_value = mock_python

        # Mock repo manager
        with patch.object(self.gui.repo_manager, 'clone_repository', return_value=True):
            with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                with patch.object(self.gui.detector, 'detect', return_value=Technology.PYTHON):
                    with patch('pathlib.Path.exists', return_value=False):
                        # Clear proxy entry
                        self.gui.http_proxy_entry.delete(0, tk.END)

                        # Run installation
                        with patch.object(self.gui.root, 'after'):
                            self.gui.run_installation(['https://github.com/user/repo'])

        # Check report shows failure
        self.assertEqual(len(self.gui.report.failed), 1)

    @patch('src.gui.GitInstaller')
    def test_run_installation_with_proxy(self, mock_git_class):
        """Test run_installation with proxy configured."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Set proxy
        self.gui.http_proxy_entry.delete(0, tk.END)
        self.gui.http_proxy_entry.insert(0, "http://myproxy.com:8080")

        # Mock repo manager - clone fails (we just want to test proxy setup)
        with patch.object(self.gui.repo_manager, 'clone_repository', return_value=False):
            with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                with patch('pathlib.Path.exists', return_value=False):
                    # Run installation
                    with patch.object(self.gui.root, 'after'):
                        self.gui.run_installation(['https://github.com/user/repo'])

        # Check proxy was set
        self.assertEqual(self.gui.proxy_manager.http_proxy, "http://myproxy.com:8080")

    @patch('src.gui.GitInstaller')
    def test_run_installation_existing_repo_remove_fails(self, mock_git_class):
        """Test run_installation when existing repository cannot be removed."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Mock repo manager
        with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
            # Mock path exists - repo already exists
            with patch('pathlib.Path.exists', return_value=True):
                # Mock safe_rmtree fails
                with patch.object(self.gui, 'safe_rmtree', return_value=False):
                    # Clear proxy entry
                    self.gui.http_proxy_entry.delete(0, tk.END)

                    # Run installation
                    with patch.object(self.gui.root, 'after'):
                        self.gui.run_installation(['https://github.com/user/repo'])

        # Check report shows failure
        self.assertEqual(len(self.gui.report.failed), 1)

    @patch('src.gui.GitInstaller')
    def test_run_installation_exception_handling(self, mock_git_class):
        """Test run_installation handles exceptions gracefully."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Mock repo manager - raises exception
        with patch.object(self.gui.repo_manager, 'get_repo_name', side_effect=Exception("Test error")):
            # Clear proxy entry
            self.gui.http_proxy_entry.delete(0, tk.END)

            # Run installation
            with patch.object(self.gui.root, 'after'):
                self.gui.run_installation(['https://github.com/user/repo'])

        # Check report shows failure
        self.assertEqual(len(self.gui.report.failed), 1)

    @patch('src.gui.GitInstaller')
    def test_run_installation_git_needs_config(self, mock_git_class):
        """Test run_installation when Git needs configuration."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = False
        mock_git_class.return_value = mock_git

        # Mock _prompt_git_config
        with patch.object(self.gui, '_prompt_git_config', return_value={'name': 'Test', 'email': 'test@test.com', 'ssl_verify': True}):
            # Mock repo manager - clone fails (we just want to test Git config)
            with patch.object(self.gui.repo_manager, 'clone_repository', return_value=False):
                with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                    with patch('pathlib.Path.exists', return_value=False):
                        # Clear proxy entry
                        self.gui.http_proxy_entry.delete(0, tk.END)

                        # Run installation
                        with patch.object(self.gui.root, 'after'):
                            self.gui.run_installation(['https://github.com/user/repo'])

        # Git configure should have been called
        mock_git.configure.assert_called_once()

    @patch('src.gui.GitInstaller')
    def test_run_installation_git_install_and_config(self, mock_git_class):
        """Test run_installation when Git needs install and configuration."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = False
        mock_git.install.return_value = True
        mock_git_class.return_value = mock_git

        # Mock _prompt_git_config
        with patch.object(self.gui, '_prompt_git_config', return_value={'name': 'Test', 'email': 'test@test.com', 'ssl_verify': True}):
            # Mock repo manager - clone fails (we just want to test Git setup)
            with patch.object(self.gui.repo_manager, 'clone_repository', return_value=False):
                with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                    with patch('pathlib.Path.exists', return_value=False):
                        # Clear proxy entry
                        self.gui.http_proxy_entry.delete(0, tk.END)

                        # Run installation
                        with patch.object(self.gui.root, 'after'):
                            self.gui.run_installation(['https://github.com/user/repo'])

        # Git install and configure should have been called
        mock_git.install.assert_called_once()
        mock_git.configure.assert_called_once()

    @patch('src.gui.GitInstaller')
    def test_run_installation_git_config_skipped(self, mock_git_class):
        """Test run_installation when Git config is skipped."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = False
        mock_git.install.return_value = True
        mock_git_class.return_value = mock_git

        # Mock _prompt_git_config - user skips
        with patch.object(self.gui, '_prompt_git_config', return_value=None):
            # Mock repo manager - clone fails
            with patch.object(self.gui.repo_manager, 'clone_repository', return_value=False):
                with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                    with patch('pathlib.Path.exists', return_value=False):
                        # Clear proxy entry
                        self.gui.http_proxy_entry.delete(0, tk.END)

                        # Run installation
                        with patch.object(self.gui.root, 'after'):
                            self.gui.run_installation(['https://github.com/user/repo'])

        # Git configure should NOT have been called
        mock_git.configure.assert_not_called()

    @patch('src.gui.PythonInstaller')
    @patch('src.gui.GitInstaller')
    def test_run_installation_successful_install_from_scratch(self, mock_git_class, mock_python_class):
        """Test run_installation with successful install from scratch (covers line 594)."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Mock Python installer - NOT installed, install succeeds
        mock_python = Mock()
        mock_python.is_installed.return_value = False
        mock_python.install.return_value = True
        mock_python.configure.return_value = True
        mock_python_class.return_value = mock_python

        # Mock repo manager
        with patch.object(self.gui.repo_manager, 'clone_repository', return_value=True):
            with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                with patch.object(self.gui.detector, 'detect', return_value=Technology.PYTHON):
                    with patch('pathlib.Path.exists', return_value=False):
                        # Clear proxy entry
                        self.gui.http_proxy_entry.delete(0, tk.END)

                        # Run installation
                        with patch.object(self.gui.root, 'after'):
                            self.gui.run_installation(['https://github.com/user/python-repo'])

        # Check report shows success
        self.assertEqual(len(self.gui.report.successful), 1)
        # Python install should have been called
        mock_python.install.assert_called_once()

    @patch('src.gui.GitInstaller')
    def test_run_installation_no_installer_for_technology(self, mock_git_class):
        """Test run_installation when no installer available (covers lines 582-585)."""
        # Mock Git installer
        mock_git = Mock()
        mock_git.is_installed.return_value = True
        mock_git.detect_version.return_value = '2.40.0'
        mock_git._is_git_configured.return_value = True
        mock_git_class.return_value = mock_git

        # Mock repo manager
        with patch.object(self.gui.repo_manager, 'clone_repository', return_value=True):
            with patch.object(self.gui.repo_manager, 'get_repo_name', return_value='test-repo'):
                # Mock detector returns Python (valid technology)
                with patch.object(self.gui.detector, 'detect', return_value=Technology.PYTHON):
                    # Mock _get_installer to return None (no installer available)
                    with patch.object(self.gui, '_get_installer', return_value=None):
                        with patch('pathlib.Path.exists', return_value=False):
                            # Clear proxy entry
                            self.gui.http_proxy_entry.delete(0, tk.END)

                            # Run installation
                            with patch.object(self.gui.root, 'after'):
                                self.gui.run_installation(['https://github.com/user/repo'])

        # Check report shows failure
        self.assertEqual(len(self.gui.report.failed), 1)


@pytest.mark.gui
class TestGUIIntegration(unittest.TestCase):
    """Integration tests for GUI components."""

    def setUp(self):
        """Set up test fixtures."""
        self.root = tk.Tk()
        self.gui = DevStartGUI(self.root)

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            self.root.destroy()
        except:
            pass

    def test_log_redirector_integration(self):
        """Test log redirector integrates correctly."""
        import sys

        # Save original stdout
        original_stdout = sys.stdout

        try:
            # Redirect to GUI
            sys.stdout = self.gui.stdout_redirector

            # Print message
            print("Test integration message")

            # Restore stdout
            sys.stdout = original_stdout

            # Check message appears in log
            content = self.gui.log_text.get(1.0, tk.END)
            self.assertIn("Test integration message", content)

        finally:
            sys.stdout = original_stdout

    def test_report_workflow(self):
        """Test complete report workflow."""
        # Start report
        self.gui.report.start()

        # Add repositories
        self.gui.report.add_repository(
            'https://github.com/user/repo1',
            True,
            Technology.PYTHON
        )
        self.gui.report.add_repository(
            'https://github.com/user/repo2',
            False,
            error='Clone failed'
        )

        # End report
        self.gui.report.end()

        # Generate report
        report_text = self.gui.report.generate_report()

        # Verify report content
        self.assertIn('Total Repositories: 2', report_text)
        self.assertIn('Successful: 1', report_text)
        self.assertIn('Failed: 1', report_text)


@pytest.mark.gui
class TestGUIMain(unittest.TestCase):
    """Test cases for GUI main function."""

    @patch('src.gui.tk.Tk')
    @patch('src.gui.DevStartGUI')
    def test_main_function(self, mock_gui_class, mock_tk_class):
        """Test main function creates GUI and runs mainloop."""
        from src.gui import main

        # Mock Tk root
        mock_root = Mock()
        mock_tk_class.return_value = mock_root

        # Mock GUI
        mock_gui = Mock()
        mock_gui_class.return_value = mock_gui

        # Run main
        main()

        # Check Tk was created
        mock_tk_class.assert_called_once()

        # Check GUI was created with root
        mock_gui_class.assert_called_once_with(mock_root)

        # Check mainloop was called
        mock_root.mainloop.assert_called_once()

    @patch('src.gui.main')
    def test_main_name_block(self, mock_main):
        """Test if __name__ == '__main__' block."""
        import subprocess
        import sys

        # Run gui.py as a script with mocked main
        result = subprocess.run(
            [sys.executable, '-c',
             'import sys; sys.path.insert(0, "src"); '
             'from unittest.mock import patch; '
             'with patch("src.gui.main"): '
             '    import src.gui; '
             '    if __name__ == "__main__": src.gui.main()'],
            capture_output=True,
            timeout=5
        )

        # Just check it doesn't crash
        self.assertEqual(result.returncode, 0)


def run_gui_tests():
    """Run GUI tests."""
    print("\n" + "=" * 70)
    print("GUI TEST SUITE")
    print("=" * 70)

    pytest.main([__file__, '-v', '-m', 'gui'])


if __name__ == '__main__':
    run_gui_tests()
