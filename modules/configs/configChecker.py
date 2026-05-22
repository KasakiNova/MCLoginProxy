# coding=utf-8
from modules.utils.logger import error as log_error


def validate_config(config: dict) -> bool:
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
                        errors.append(
                            f"{section}.{field}: Expected {expected_type.__name__}, got {type(actual_value).__name__}"
                        )

    for key, server_config in config.items():
        if key.startswith("Server.") and isinstance(server_config, dict):
            for field, expected_type in schema["Server"].items():
                if field in server_config:
                    actual_value = server_config[field]
                    if not isinstance(actual_value, expected_type):
                        errors.append(
                            f"{key}.{field}: Expected {expected_type.__name__}, got {type(actual_value).__name__}"
                        )

    if errors:
        for err in errors:
            log_error(err)
        return False
    else:
        return True

