# coding=utf-8
import os

sep = os.sep
runningDir = os.getcwd()
configDir = os.path.join(runningDir, 'config')
webDir = os.path.join(configDir, 'static')
configFileName = "config.toml"
configFilePath = os.path.join(configDir, configFileName)
accountsInfoDB = os.path.join(webDir,'accounts.db')
debugMode = False

cfgContext = {}
publickey= {}
proxies = {}
