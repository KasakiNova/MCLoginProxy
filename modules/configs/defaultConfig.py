# coding=utf-8
# This is default config.toml context
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
address="127.0.0.1:8080"

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
    file_path = path
    with open(file_path, 'w') as configfile:
        configfile.write(default_config)