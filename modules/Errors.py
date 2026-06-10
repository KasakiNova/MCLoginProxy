# coding=utf-8
"""Custom exception classes for MCLoginProxy."""
from typing import Optional


class ErrorInGettingPublickeysFromMojang(Exception):
    """Failed to retrieve valid publickeys from Mojang's API."""

    def __init__(self, error_info: str) -> None:
        super().__init__(error_info)
        self.errorInfo = error_info

    def __str__(self) -> str:
        return self.errorInfo


class ErrorInGettingPublickeysFromLittleSkin(Exception):
    """Failed to retrieve valid publickeys from LittleSkin's API."""

    def __init__(self, error_info: str) -> None:
        super().__init__(error_info)
        self.errorInfo = error_info

    def __str__(self) -> str:
        return self.errorInfo


class FailureToFetchProfile(Exception):
    """Unable to fetch a player profile from the remote auth server."""

    def __init__(self, error_info: str) -> None:
        super().__init__(error_info)
        self.errorInfo = error_info

    def __str__(self) -> str:
        return self.errorInfo


class ProxyError(Exception):
    """Proxy connectivity check failed."""

    def __init__(self) -> None:
        super().__init__("Proxy Error")
        self.errorInfo = "Proxy Error"

    def __str__(self) -> str:
        return self.errorInfo


class PlayerIsBaned(Exception):
    """The player is banned on the current auth server."""

    def __init__(self, error_info: str) -> None:
        super().__init__(error_info)
        self.errorInfo = error_info

    def __str__(self) -> str:
        return self.errorInfo
