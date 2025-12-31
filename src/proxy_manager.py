"""Proxy configuration manager for corporate environments."""
import os
import re
from typing import Optional, Dict

from .constants import PROXY_URL_PATTERN
from .exceptions import InvalidProxyURLError
from .logger import get_logger

logger = get_logger(__name__)


class ProxyManager:
    """Manages HTTP/HTTPS proxy configuration."""

    def __init__(self):
        self.http_proxy: Optional[str] = None
        self.https_proxy: Optional[str] = None

    def validate_proxy_url(self, url: str) -> bool:
        """
        Validate a proxy URL.

        Args:
            url: Proxy URL to validate

        Returns:
            True if valid

        Raises:
            InvalidProxyURLError: If URL is invalid
        """
        if not url or not isinstance(url, str):
            raise InvalidProxyURLError(url or '')

        url = url.strip()

        if not re.match(PROXY_URL_PATTERN, url):
            raise InvalidProxyURLError(url)

        # Basic format check: should have host and optionally port
        if '://' not in url:
            raise InvalidProxyURLError(url)

        # Extract host:port part
        host_part = url.split('://')[1].rstrip('/')

        # Check for valid host
        if not host_part or host_part.startswith(':'):
            raise InvalidProxyURLError(url)

        return True

    def set_proxy(self, http_proxy: Optional[str] = None, https_proxy: Optional[str] = None) -> None:
        """
        Configure proxy settings.

        Args:
            http_proxy: HTTP proxy URL
            https_proxy: HTTPS proxy URL

        Raises:
            InvalidProxyURLError: If any proxy URL is invalid
        """
        if http_proxy:
            self.validate_proxy_url(http_proxy)
            self.http_proxy = http_proxy
            os.environ['HTTP_PROXY'] = http_proxy
            os.environ['http_proxy'] = http_proxy
            logger.info(f"HTTP proxy configured: {http_proxy}")

        if https_proxy:
            self.validate_proxy_url(https_proxy)
            self.https_proxy = https_proxy
            os.environ['HTTPS_PROXY'] = https_proxy
            os.environ['https_proxy'] = https_proxy
            logger.info(f"HTTPS proxy configured: {https_proxy}")

    def get_proxy_dict(self) -> Dict[str, str]:
        """
        Get proxy configuration as dictionary for requests library.

        Returns:
            Dictionary with 'http' and 'https' keys
        """
        proxies = {}
        if self.http_proxy:
            proxies['http'] = self.http_proxy
        if self.https_proxy:
            proxies['https'] = self.https_proxy
        return proxies

    def clear_proxy(self) -> None:
        """Clear proxy configuration."""
        self.http_proxy = None
        self.https_proxy = None

        for key in ['HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy']:
            os.environ.pop(key, None)

        logger.info("Proxy configuration cleared")
