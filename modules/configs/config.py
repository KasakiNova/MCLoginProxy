# coding=utf-8
"""Config file creation, validation, and loading for MCLoginProxy.

Handles ``config/config.toml``:
- Creates a default TOML file if missing.
- Validates every section/field type before use.
- Provides the ``Config`` class for init and read operations.
"""
import os
import sys

try:
    import tomllib
except ImportError:
    import tomli as tomllib

import modules.globalVariables as gVar
from modules.utils.logger import info, error

default_config = """[General]
# Enable Debug Mode
# false: info, true: debug,
# default: false
debug=false

# Binding IP
# default: "127.0.0.1"
ip = "127.0.0.1"

# Service listening port
# default: 30000
port=30000

# Check Publickeys time
# Default: 7200
# 0 is no check for updates
CheckKeysTime=7200

# Disable Show System Info
# Default: false
# If true, will not show system info in console
disableSysInfo=false

[Log]
# Save Logs
# default: false
save-log=false

# Log save directory
# default: logs
log_dir = "logs"

# Max save log files
# default: 5
max_save_log = 5

[Proxy]
# Enable Proxy
# Default: false
enable=false

# Proxy Address
# Protocol input required
# Examples: address="http://127.0.0.1:8080"
# Supported Protocols: http, https
address="http://127.0.0.1:8080"

# Enable Auth
# Default: false
enable_auth=false

# Proxy Auth Username
username=""

# Proxy Auth Password
password=""

# Auth Servers
# ServerType:
# Mojang: Mojang Official Auth Server
# Blessing: Blessing Skin Server Yggdrasil API

[Server.0]
# Mojang Official Server
Name="Mojang"
ServerType="Mojang"
NeedProxy=false

[Server.1]
# LittleSkin Server
Name="LittleSkin"
ServerType="Blessing"
NeedProxy=false
Url="https://littleskin.cn/api/yggdrasil"

"""


def create_config_file(path: str) -> None:
    """Write the default config to *path*, creating parent dirs if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as configfile:
        configfile.write(default_config)


def validate_config(config: dict) -> bool:
    """Return True if *config* matches the expected schema.

    Logs every type mismatch via the error logger.
    """
    schema = {
        "General": {
            "debug": bool,
            "ip": str,
            "port": int,
            "CheckKeysTime": int
        },
        "Log": {
            "save-log": bool,
            "log_dir": str,
            "max_save_log": int
        },
        "Proxy": {
            "enable": bool,
            "address": str,
            "enable_auth": bool,
            "username": str,
            "password": str
        },
        "Server": {
            "Name": str,
            "ServerType": str,
            "NeedProxy": bool,
            "Url": str
        }
    }

    errors = []

    for section, fields in schema.items():
        if section == "Server":
            continue
        if section in config:
            for field, expected_type in fields.items():
                if field in config[section]:
                    actual_value = config[section][field]
                    if not isinstance(actual_value, expected_type):
                        msg = (
                            f"{section}.{field}: "
                            f"Expected {expected_type.__name__}, "
                            f"got {type(actual_value).__name__}"
                        )
                        errors.append(msg)

    for key, server_config in config.items():
        if key.startswith("Server.") and isinstance(server_config, dict):
            for field, expected_type in schema["Server"].items():
                if field in server_config:
                    actual_value = server_config[field]
                    if not isinstance(actual_value, expected_type):
                        msg = (
                            f"{key}.{field}: "
                            f"Expected {expected_type.__name__}, "
                            f"got {type(actual_value).__name__}"
                        )
                        errors.append(msg)

    if errors:
        for err in errors:
            error(err)
        return False
    return True


class Config:
    """Manage ``config/config.toml`` lifecycle."""

    def __init__(self) -> None:
        self._file_name = gVar.configFilePath

    def init(self) -> bool:
        """Ensure config file exists and is readable; create default if missing.

        Returns:
            True when config is ready for reading.
        """
        if not os.path.exists(self._file_name):
            create_config_file(self._file_name)
            info("Created default config file")
            return True

        if not os.path.isfile(self._file_name):
            error("config.toml not file")
            return False

        if not os.access(self._file_name, os.R_OK):
            error("config.toml not readable")
            return False
        return True

    def read(self) -> dict:
        """Parse and validate the config file; return the resulting dict."""
        with open(self._file_name, 'rb') as fff:
            f = tomllib.load(fff)
            if not validate_config(f):
                sys.exit("Config File is incorrect")
            try:
                if f["General"]["debug"]:
                    gVar.debugMode = True
            except KeyError:
                gVar.debugMode = False
            return f
