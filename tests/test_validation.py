"""Tests for validation functionality."""
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from src.exceptions import (
    InvalidURLError,
    InvalidProxyURLError,
    InvalidEnvironmentVariableError,
)
from src.repo_manager import RepositoryManager
from src.proxy_manager import ProxyManager
from src.env_manager import EnvironmentManager


class TestURLValidation(unittest.TestCase):
    """Test cases for URL validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.proxy_manager = ProxyManager()
        self.repo_manager = RepositoryManager(self.proxy_manager)

    def test_valid_https_url(self):
        """Test valid HTTPS URL passes validation."""
        url = "https://github.com/user/repo"
        result = self.repo_manager.validate_repo_url(url)
        self.assertTrue(result)

    def test_valid_http_url(self):
        """Test valid HTTP URL passes validation."""
        url = "http://github.com/user/repo"
        result = self.repo_manager.validate_repo_url(url)
        self.assertTrue(result)

    def test_valid_git_url(self):
        """Test valid git:// URL passes validation."""
        url = "git://github.com/user/repo"
        result = self.repo_manager.validate_repo_url(url)
        self.assertTrue(result)

    def test_empty_url_raises_error(self):
        """Test empty URL raises InvalidURLError."""
        with self.assertRaises(InvalidURLError):
            self.repo_manager.validate_repo_url("")

    def test_none_url_raises_error(self):
        """Test None URL raises InvalidURLError."""
        with self.assertRaises(InvalidURLError):
            self.repo_manager.validate_repo_url(None)

    def test_invalid_scheme_raises_error(self):
        """Test invalid URL scheme raises InvalidURLError."""
        with self.assertRaises(InvalidURLError) as context:
            self.repo_manager.validate_repo_url("ftp://github.com/user/repo")
        self.assertIn("scheme", str(context.exception).lower())

    def test_missing_host_raises_error(self):
        """Test URL without host raises InvalidURLError."""
        with self.assertRaises(InvalidURLError):
            self.repo_manager.validate_repo_url("https:///user/repo")

    def test_url_with_shell_metacharacters_raises_error(self):
        """Test URL with shell metacharacters raises InvalidURLError."""
        dangerous_urls = [
            "https://github.com/user/repo;rm -rf /",
            "https://github.com/user/repo|cat /etc/passwd",
            "https://github.com/user/repo`whoami`",
            "https://github.com/user/repo$HOME",
        ]
        for url in dangerous_urls:
            with self.assertRaises(InvalidURLError):
                self.repo_manager.validate_repo_url(url)

    def test_url_with_directory_traversal_raises_error(self):
        """Test URL with directory traversal raises InvalidURLError."""
        with self.assertRaises(InvalidURLError):
            self.repo_manager.validate_repo_url("https://github.com/user/../repo")

    def test_url_without_path_raises_error(self):
        """Test URL without path raises InvalidURLError."""
        with self.assertRaises(InvalidURLError):
            self.repo_manager.validate_repo_url("https://github.com/")

    def test_url_with_git_suffix(self):
        """Test URL with .git suffix passes validation."""
        url = "https://github.com/user/repo.git"
        result = self.repo_manager.validate_repo_url(url)
        self.assertTrue(result)


class TestProxyURLValidation(unittest.TestCase):
    """Test cases for proxy URL validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.proxy_manager = ProxyManager()

    def test_valid_http_proxy(self):
        """Test valid HTTP proxy URL passes validation."""
        result = self.proxy_manager.validate_proxy_url("http://proxy.example.com:8080")
        self.assertTrue(result)

    def test_valid_https_proxy(self):
        """Test valid HTTPS proxy URL passes validation."""
        result = self.proxy_manager.validate_proxy_url("https://proxy.example.com:8080")
        self.assertTrue(result)

    def test_proxy_without_port(self):
        """Test proxy URL without port passes validation."""
        result = self.proxy_manager.validate_proxy_url("http://proxy.example.com")
        self.assertTrue(result)

    def test_empty_proxy_url_raises_error(self):
        """Test empty proxy URL raises InvalidProxyURLError."""
        with self.assertRaises(InvalidProxyURLError):
            self.proxy_manager.validate_proxy_url("")

    def test_none_proxy_url_raises_error(self):
        """Test None proxy URL raises InvalidProxyURLError."""
        with self.assertRaises(InvalidProxyURLError):
            self.proxy_manager.validate_proxy_url(None)

    def test_invalid_proxy_scheme_raises_error(self):
        """Test invalid proxy scheme raises InvalidProxyURLError."""
        with self.assertRaises(InvalidProxyURLError):
            self.proxy_manager.validate_proxy_url("ftp://proxy.example.com:8080")

    def test_proxy_without_host_raises_error(self):
        """Test proxy URL without host raises InvalidProxyURLError."""
        with self.assertRaises(InvalidProxyURLError):
            self.proxy_manager.validate_proxy_url("http://:8080")

    def test_set_proxy_validates_url(self):
        """Test set_proxy validates URL before setting."""
        with self.assertRaises(InvalidProxyURLError):
            self.proxy_manager.set_proxy(http_proxy="invalid-url")

    def test_set_valid_proxy(self):
        """Test setting valid proxy URLs."""
        self.proxy_manager.set_proxy(
            http_proxy="http://proxy.example.com:8080",
            https_proxy="https://proxy.example.com:8080"
        )
        self.assertEqual(self.proxy_manager.http_proxy, "http://proxy.example.com:8080")
        self.assertEqual(self.proxy_manager.https_proxy, "https://proxy.example.com:8080")


class TestEnvironmentVariableValidation(unittest.TestCase):
    """Test cases for environment variable name validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.env_manager = EnvironmentManager(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_valid_env_var_name(self):
        """Test valid environment variable names pass validation."""
        valid_names = [
            "MY_VAR",
            "DATABASE_URL",
            "_PRIVATE_VAR",
            "var123",
            "A",
            "a_b_c",
        ]
        for name in valid_names:
            result = self.env_manager.validate_env_var_name(name)
            self.assertTrue(result)

    def test_empty_env_var_name_raises_error(self):
        """Test empty environment variable name raises error."""
        with self.assertRaises(InvalidEnvironmentVariableError):
            self.env_manager.validate_env_var_name("")

    def test_none_env_var_name_raises_error(self):
        """Test None environment variable name raises error."""
        with self.assertRaises(InvalidEnvironmentVariableError):
            self.env_manager.validate_env_var_name(None)

    def test_env_var_starting_with_number_raises_error(self):
        """Test environment variable starting with number raises error."""
        with self.assertRaises(InvalidEnvironmentVariableError):
            self.env_manager.validate_env_var_name("123_VAR")

    def test_env_var_with_special_chars_raises_error(self):
        """Test environment variable with special characters raises error."""
        invalid_names = [
            "MY-VAR",
            "MY.VAR",
            "MY VAR",
            "MY@VAR",
            "MY$VAR",
        ]
        for name in invalid_names:
            with self.assertRaises(InvalidEnvironmentVariableError):
                self.env_manager.validate_env_var_name(name)

    def test_create_env_file_validates_names(self):
        """Test create_env_file validates variable names."""
        with self.assertRaises(InvalidEnvironmentVariableError):
            self.env_manager.create_env_file({"INVALID-NAME": "value"})

    def test_append_to_env_validates_name(self):
        """Test append_to_env validates variable name."""
        with self.assertRaises(InvalidEnvironmentVariableError):
            self.env_manager.append_to_env("INVALID-NAME", "value")


class TestExceptionHierarchy(unittest.TestCase):
    """Test cases for exception hierarchy."""

    def test_invalid_url_error_inheritance(self):
        """Test InvalidURLError inherits from correct base classes."""
        from src.exceptions import ValidationError, DevStartError
        error = InvalidURLError("http://test", "test reason")
        self.assertIsInstance(error, ValidationError)
        self.assertIsInstance(error, DevStartError)

    def test_invalid_proxy_url_error_inheritance(self):
        """Test InvalidProxyURLError inherits from correct base classes."""
        from src.exceptions import ValidationError, DevStartError
        error = InvalidProxyURLError("invalid")
        self.assertIsInstance(error, ValidationError)
        self.assertIsInstance(error, DevStartError)

    def test_invalid_env_var_error_inheritance(self):
        """Test InvalidEnvironmentVariableError inherits from correct base classes."""
        from src.exceptions import ValidationError, DevStartError
        error = InvalidEnvironmentVariableError("invalid")
        self.assertIsInstance(error, ValidationError)
        self.assertIsInstance(error, DevStartError)

    def test_exception_message_formatting(self):
        """Test exception message formatting with details."""
        from src.exceptions import DevStartError
        error = DevStartError("Main message", details="Additional details")
        error_str = str(error)
        self.assertIn("Main message", error_str)
        self.assertIn("Additional details", error_str)


if __name__ == '__main__':
    unittest.main()
