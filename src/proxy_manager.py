"""Proxy configuration manager for corporate environments."""
import os
from typing import Optional, Dict


class ProxyManager:
    """Manages HTTP/HTTPS proxy configuration."""

    def __init__(self):
        self.http_proxy: Optional[str] = None
        self.https_proxy: Optional[str] = None

    def set_proxy(self, http_proxy: Optional[str] = None, https_proxy: Optional[str] = None):
        """Configure proxy settings."""
        self.http_proxy = http_proxy
        self.https_proxy = https_proxy

        if http_proxy:
            os.environ['HTTP_PROXY'] = http_proxy
            os.environ['http_proxy'] = http_proxy

        if https_proxy:
            os.environ['HTTPS_PROXY'] = https_proxy
            os.environ['https_proxy'] = https_proxy

    def get_proxy_dict(self) -> Dict[str, str]:
        """Get proxy configuration as dictionary for requests library."""
        proxies = {}
        if self.http_proxy:
            proxies['http'] = self.http_proxy
        if self.https_proxy:
            proxies['https'] = self.https_proxy
        return proxies

    def clear_proxy(self):
        """Clear proxy configuration."""
        self.http_proxy = None
        self.https_proxy = None

        for key in ['HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy']:
            os.environ.pop(key, None)
