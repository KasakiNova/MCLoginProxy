# coding=utf-8
"""HTTP/HTTPS proxy support for outbound requests."""
import requests

import modules.globalVariables as gVar
from modules.Errors import ProxyError


class Proxies:
    """Build and validate proxy configuration from ``config.toml``."""

    def __init__(self) -> None:
        self.__proxies = {}
        proxy_settings = gVar.cfgContext['Proxy']
        if proxy_settings['enable']:
            if proxy_settings['enable_auth']:
                protocol = proxy_settings['address'].split("://")[0]
                link = proxy_settings['address'].split("://")[1]
                self.__proxies = {
                    "http": (
                        f"{protocol}://"
                        f"{proxy_settings['username']}:"
                        f"{proxy_settings['password']}@"
                        f"{link}"
                    ),
                    "https": (
                        f"{protocol}://"
                        f"{proxy_settings['username']}:"
                        f"{proxy_settings['password']}@"
                        f"{link}"
                    ),
                }
            else:
                self.__proxies = {
                    "http": proxy_settings['address'],
                    "https": proxy_settings['address']
                }
        gVar.proxies = self.__proxies

    def check_proxies(self,
                      url: str = "https://api.myip.la") -> bool:
        """Verify proxy connectivity by making a test request.

        Returns True when the proxy responds with HTTP 200.
        """
        try:
            response = requests.get(
                url=url, proxies=self.__proxies, timeout=10
            )
            if response.status_code == 200:
                return True
            raise ProxyError
        except (requests.exceptions.RequestException, ProxyError):
            return False
