# coding=utf-8
import requests

import modules.globalVariables as gVar
from modules.Errors import ProxyError


class Proxies:
    def __init__(self):
        self.__proxies = {}
        proxy_settings = gVar.cfgContext['Proxy']
        if proxy_settings['enable']:
            # If enable auth
            if proxy_settings['enable_auth']:
                protocol = proxy_settings['address'].split("://")[0]
                link = proxy_settings['address'].split("://")[1]
                self.__proxies = {
                    "http": f"{protocol}://{proxy_settings['username']}:{proxy_settings['password']}@{link}",
                    "https": f"{protocol}://{proxy_settings['username']}:{proxy_settings['password']}@{link}",
                }
            # this is no auths proxies
            else:
                self.__proxies = {
                    "http": f"{proxy_settings['address']}",
                    "https": f"{proxy_settings['address']}"
                }
        gVar.proxies = self.__proxies

    def check_proxies(self, url = "https://api.myip.la"):
        try:
            response = requests.get(url=url, proxies=self.__proxies, timeout=10)
            if response.status_code == 200:
                return True
            else:
                raise ProxyError
        except (requests.exceptions.RequestException, ProxyError):
            return False