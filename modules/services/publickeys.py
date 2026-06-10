# coding=utf-8
"""Periodic publickeys fetcher for Minecraft authentication.

Retrieves the public key list from Mojang (falling back to LittleSkin)
and caches it to ``config/static/publickeys.json``.  A background
thread keeps the cache up to date when ``CheckKeysTime`` > 0.
"""
import json
import os
import threading
from json import JSONDecodeError
from time import sleep

import requests

import modules.globalVariables as gVar
from modules.Errors import ErrorInGettingPublickeysFromMojang, ErrorInGettingPublickeysFromLittleSkin
from modules.utils.logger import info, error


class PublicKeys:
    """Manage Minecraft publickeys cache."""

    def __init__(self) -> None:
        self.__keys = {}
        self.__staticDir = gVar.webDir
        self.__keyFile = os.path.join(self.__staticDir, 'publickeys.json')
        self.__check_time = gVar.cfgContext["General"]["CheckKeysTime"]
        self.__proxy_enable = gVar.cfgContext["Proxy"]["enable"]
        self.__proxies = gVar.proxies
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cached publickeys from disk (if any)."""
        try:
            if os.path.isfile(self.__keyFile) and os.path.getsize(self.__keyFile) > 0:
                with open(self.__keyFile, 'r') as keyFile:
                    self.__keys = json.loads(keyFile.read())
                gVar.publickey = self.__keys
        except JSONDecodeError:
            pass
        except FileNotFoundError:
            pass

    def start_thread(self) -> None:
        """Perform initial fetch, then start periodic refresh if configured."""
        if not self.__keys or not self.check_key():
            self.get_key()
            gVar.publickey = self.__keys
            self.write_json_to_file()

        if self.__check_time == 0:
            info("PublicKeys Loaded")
        else:
            thread = threading.Thread(target=self._thread)
            thread.daemon = True
            thread.start()
            info("Update PublicKeys Services Loaded")

    def _thread(self) -> None:
        """Background loop that periodically refreshes the publickeys."""
        sleep(5)
        while True:
            self.get_key()
            if self.__keys != gVar.publickey:
                gVar.publickey = self.__keys
                self.write_json_to_file()
            sleep(self.__check_time)

    def write_json_to_file(self) -> None:
        """Persist the current publickeys to disk."""
        with open(self.__keyFile, 'w') as file:
            file.write(json.dumps(self.__keys, indent=4, ensure_ascii=False))

    def get_key(self) -> None:
        """Fetch publickeys from Mojang, falling back to LittleSkin."""
        mojang_server = "https://api.minecraftservices.com/publickeys"
        little_skin = (
            "https://littleskin.cn/api/yggdrasil/"
            "minecraftservices/publickeys"
        )
        try:
            response = self._request(mojang_server)
            if response is not None and response.status_code == 200:
                self.__keys = response.json()
                if self.check_key():
                    gVar.publickey = self.__keys
                else:
                    raise ErrorInGettingPublickeysFromMojang(
                        "Unable to get publickeys from mojang server"
                    )
            else:
                raise ErrorInGettingPublickeysFromMojang(
                    "Unable to get publickeys from mojang server"
                )
        except ErrorInGettingPublickeysFromMojang as e:
            error(str(e))
            try:
                response = self._request(little_skin)
                if response is not None and response.status_code == 200:
                    self.__keys = response.json()
                    if self.check_key():
                        gVar.publickey = self.__keys
                    else:
                        raise ErrorInGettingPublickeysFromLittleSkin(
                            "Unable to get publickeys from LittleSkin server"
                        )
                else:
                    raise ErrorInGettingPublickeysFromLittleSkin(
                        "Unable to get publickeys from LittleSkin server"
                    )
            except ErrorInGettingPublickeysFromLittleSkin as e:
                error(str(e))

    def check_key(self) -> bool:
        """Validate the structure of the fetched publickeys dict."""
        try:
            for key in self.__keys:
                expected = {"profilePropertyKeys", "playerCertificateKeys",
                            "authenticationKeys"}
                if key not in expected:
                    return False
                if not isinstance(self.__keys[key], list):
                    return False
                for item in self.__keys[key]:
                    if not isinstance(item, dict) or "publicKey" not in item:
                        return False
            return True
        except (TypeError, AttributeError):
            return False

    def _request(self, url: str):
        """GET *url* (with proxy if enabled), returning Response or None."""
        try:
            if self.__proxy_enable:
                return requests.get(url, proxies=self.__proxies, timeout=10)
            else:
                return requests.get(url, timeout=10)
        except requests.exceptions.RequestException:
            return None
