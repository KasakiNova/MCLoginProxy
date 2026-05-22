# coding=utf-8
import sys
import os

# If Python Version is Lower than 3.11 or not found tomllib, this well be import tomli to change tomllib
try:
    import tomllib
except ImportError:
    import tomli as tomllib

import modules.globalVariables as gVar
from modules.configs.defaultConfig import create_config_file
from modules.configs.configChecker import validate_config
from modules.utils.logger import info, error

class Config:
    def __init__(self):
        self._file_name = gVar.configFileName
        self._content = {}

    # Setup config
    # return Ture or False
    # Ture is Success
    # False is Failure
    def init(self) -> bool:
        # If config.toml does not exist, create it
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
        with open(self._file_name, 'rb') as fff:
            f = tomllib.load(fff)
            if not validate_config(f):
                sys.exit("Config File is incorrect")
            try:
                if f["General"]["debug"] :
                    gVar.debugMode = True
            except KeyError:
                gVar.debugMode = False
            return f

