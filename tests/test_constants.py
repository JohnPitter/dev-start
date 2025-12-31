"""Tests for constants module."""
import unittest
from pathlib import Path

from src.constants import (
    BASE_DIR_NAME,
    TOOLS_DIR_NAME,
    TOOLS_SUBDIR,
    get_base_dir,
    get_tools_dir,
    DOWNLOAD_TIMEOUT,
    BUILD_TIMEOUT,
    COMMAND_TIMEOUT,
    GIT_TIMEOUT,
    DEFAULT_VERSIONS,
    DOWNLOAD_URLS,
    DOWNLOAD_CHECKSUMS,
    ALLOWED_URL_SCHEMES,
    ENV_VAR_NAME_PATTERN,
    PROXY_URL_PATTERN,
    MAX_DOWNLOAD_RETRIES,
    MAX_RMTREE_RETRIES,
    DOWNLOAD_CHUNK_SIZE,
)


class TestConstants(unittest.TestCase):
    """Test cases for constants module."""

    def test_directory_names_defined(self):
        """Test directory name constants are defined."""
        self.assertEqual(BASE_DIR_NAME, 'dev-start-projects')
        self.assertEqual(TOOLS_DIR_NAME, '.dev-start')
        self.assertEqual(TOOLS_SUBDIR, 'tools')

    def test_get_base_dir_returns_path(self):
        """Test get_base_dir returns a Path object."""
        result = get_base_dir()
        self.assertIsInstance(result, Path)
        self.assertTrue(str(result).endswith(BASE_DIR_NAME))

    def test_get_tools_dir_returns_path(self):
        """Test get_tools_dir returns a Path object."""
        result = get_tools_dir()
        self.assertIsInstance(result, Path)
        self.assertIn(TOOLS_DIR_NAME, str(result))
        self.assertIn(TOOLS_SUBDIR, str(result))

    def test_timeout_values_are_positive(self):
        """Test timeout values are positive integers."""
        self.assertGreater(DOWNLOAD_TIMEOUT, 0)
        self.assertGreater(BUILD_TIMEOUT, 0)
        self.assertGreater(COMMAND_TIMEOUT, 0)
        self.assertGreater(GIT_TIMEOUT, 0)

    def test_default_versions_defined(self):
        """Test default versions are defined for all technologies."""
        required_keys = ['java', 'python', 'nodejs', 'git', 'maven']
        for key in required_keys:
            self.assertIn(key, DEFAULT_VERSIONS)
            self.assertIsInstance(DEFAULT_VERSIONS[key], str)
            self.assertGreater(len(DEFAULT_VERSIONS[key]), 0)

    def test_download_urls_defined(self):
        """Test download URLs are defined for all technologies."""
        required_keys = ['git', 'java', 'maven', 'nodejs', 'python']
        for key in required_keys:
            self.assertIn(key, DOWNLOAD_URLS)
            self.assertIsInstance(DOWNLOAD_URLS[key], dict)

    def test_download_urls_contain_default_versions(self):
        """Test download URLs contain entries for default versions."""
        # Check Java
        self.assertIn(DEFAULT_VERSIONS['java'], DOWNLOAD_URLS['java'])

        # Check Git
        self.assertIn(DEFAULT_VERSIONS['git'], DOWNLOAD_URLS['git'])

        # Check Node.js
        self.assertIn(DEFAULT_VERSIONS['nodejs'], DOWNLOAD_URLS['nodejs'])

    def test_download_checksums_structure(self):
        """Test download checksums have correct structure."""
        self.assertIsInstance(DOWNLOAD_CHECKSUMS, dict)
        for key, value in DOWNLOAD_CHECKSUMS.items():
            self.assertIsInstance(value, dict)

    def test_allowed_url_schemes(self):
        """Test allowed URL schemes are defined."""
        self.assertIn('http', ALLOWED_URL_SCHEMES)
        self.assertIn('https', ALLOWED_URL_SCHEMES)
        self.assertIn('git', ALLOWED_URL_SCHEMES)

    def test_env_var_name_pattern_valid(self):
        """Test environment variable name pattern matches valid names."""
        import re
        valid_names = ['MY_VAR', 'DATABASE_URL', '_PRIVATE', 'var123', 'A']
        for name in valid_names:
            self.assertIsNotNone(
                re.match(ENV_VAR_NAME_PATTERN, name),
                f"Pattern should match '{name}'"
            )

    def test_env_var_name_pattern_invalid(self):
        """Test environment variable name pattern rejects invalid names."""
        import re
        invalid_names = ['123VAR', 'MY-VAR', 'MY VAR', 'MY.VAR']
        for name in invalid_names:
            self.assertIsNone(
                re.match(ENV_VAR_NAME_PATTERN, name),
                f"Pattern should not match '{name}'"
            )

    def test_proxy_url_pattern_valid(self):
        """Test proxy URL pattern matches valid URLs."""
        import re
        valid_urls = [
            'http://proxy.example.com:8080',
            'https://proxy.example.com:8080',
            'http://192.168.1.1:3128',
        ]
        for url in valid_urls:
            self.assertIsNotNone(
                re.match(PROXY_URL_PATTERN, url),
                f"Pattern should match '{url}'"
            )

    def test_retry_values_positive(self):
        """Test retry values are positive."""
        self.assertGreater(MAX_DOWNLOAD_RETRIES, 0)
        self.assertGreater(MAX_RMTREE_RETRIES, 0)

    def test_chunk_size_positive(self):
        """Test download chunk size is positive."""
        self.assertGreater(DOWNLOAD_CHUNK_SIZE, 0)


class TestDownloadURLsIntegrity(unittest.TestCase):
    """Test cases for download URL integrity."""

    def test_git_url_is_https(self):
        """Test Git download URL uses HTTPS."""
        for version, url in DOWNLOAD_URLS['git'].items():
            self.assertTrue(
                url.startswith('https://'),
                f"Git URL for version {version} should use HTTPS"
            )

    def test_java_urls_are_https(self):
        """Test Java download URLs use HTTPS."""
        for version, url in DOWNLOAD_URLS['java'].items():
            self.assertTrue(
                url.startswith('https://'),
                f"Java URL for version {version} should use HTTPS"
            )

    def test_nodejs_url_is_https(self):
        """Test Node.js download URL uses HTTPS."""
        for version, url in DOWNLOAD_URLS['nodejs'].items():
            self.assertTrue(
                url.startswith('https://'),
                f"Node.js URL for version {version} should use HTTPS"
            )

    def test_maven_urls_are_https(self):
        """Test Maven download URLs use HTTPS."""
        for version, urls in DOWNLOAD_URLS['maven'].items():
            if isinstance(urls, list):
                for url in urls:
                    self.assertTrue(
                        url.startswith('https://'),
                        f"Maven URL should use HTTPS: {url}"
                    )
            else:
                self.assertTrue(
                    urls.startswith('https://'),
                    f"Maven URL should use HTTPS: {urls}"
                )


if __name__ == '__main__':
    unittest.main()
