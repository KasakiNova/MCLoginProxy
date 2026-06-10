# coding=utf-8
"""Shared runtime globals: paths, config context, publickeys, and proxy dict.

All module-level variables are set during startup and treated as
read-only afterwards (except ``cfgContext`` and ``debugMode`` which
may be updated on ``reload``).
"""
import os

sep = os.sep
runningDir = os.getcwd()
configDir = os.path.join(runningDir, 'config')
webDir = os.path.join(configDir, 'static')
configFileName = "config.toml"
configFilePath = os.path.join(configDir, configFileName)
accountsInfoDB = os.path.join(webDir, 'accounts.db')
debugMode = False

cfgContext = {}
publickey = {}
proxies = {}
