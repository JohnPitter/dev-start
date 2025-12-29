"""Tests for proxy manager."""
import unittest
import os
from src.proxy_manager import ProxyManager


class TestProxyManager(unittest.TestCase):
    """Test cases for ProxyManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.proxy_manager = ProxyManager()
        # Clear any existing proxy settings
        self.original_env = {}
        for key in ['HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy']:
            self.original_env[key] = os.environ.get(key)
            os.environ.pop(key, None)

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    def test_set_http_proxy(self):
        """Test setting HTTP proxy."""
        proxy_url = 'http://proxy.example.com:8080'
        self.proxy_manager.set_proxy(http_proxy=proxy_url)

        self.assertEqual(self.proxy_manager.http_proxy, proxy_url)
        self.assertEqual(os.environ.get('HTTP_PROXY'), proxy_url)
        self.assertEqual(os.environ.get('http_proxy'), proxy_url)

    def test_set_https_proxy(self):
        """Test setting HTTPS proxy."""
        proxy_url = 'http://proxy.example.com:8443'
        self.proxy_manager.set_proxy(https_proxy=proxy_url)

        self.assertEqual(self.proxy_manager.https_proxy, proxy_url)
        self.assertEqual(os.environ.get('HTTPS_PROXY'), proxy_url)
        self.assertEqual(os.environ.get('https_proxy'), proxy_url)

    def test_set_both_proxies(self):
        """Test setting both HTTP and HTTPS proxies."""
        http_url = 'http://proxy.example.com:8080'
        https_url = 'http://proxy.example.com:8443'

        self.proxy_manager.set_proxy(http_proxy=http_url, https_proxy=https_url)

        self.assertEqual(self.proxy_manager.http_proxy, http_url)
        self.assertEqual(self.proxy_manager.https_proxy, https_url)

    def test_get_proxy_dict(self):
        """Test getting proxy configuration as dictionary."""
        http_url = 'http://proxy.example.com:8080'
        https_url = 'http://proxy.example.com:8443'

        self.proxy_manager.set_proxy(http_proxy=http_url, https_proxy=https_url)
        proxy_dict = self.proxy_manager.get_proxy_dict()

        self.assertEqual(proxy_dict['http'], http_url)
        self.assertEqual(proxy_dict['https'], https_url)

    def test_get_proxy_dict_empty(self):
        """Test getting empty proxy dictionary."""
        proxy_dict = self.proxy_manager.get_proxy_dict()
        self.assertEqual(proxy_dict, {})

    def test_clear_proxy(self):
        """Test clearing proxy configuration."""
        http_url = 'http://proxy.example.com:8080'
        self.proxy_manager.set_proxy(http_proxy=http_url)

        self.proxy_manager.clear_proxy()

        self.assertIsNone(self.proxy_manager.http_proxy)
        self.assertIsNone(self.proxy_manager.https_proxy)
        self.assertIsNone(os.environ.get('HTTP_PROXY'))
        self.assertIsNone(os.environ.get('http_proxy'))


if __name__ == '__main__':
    unittest.main()
