# MCLoginProxy

[English](README.md) | [简体中文](README_zh.md)

A Minecraft Java Edition Yggdrasil authentication proxy that lets premium (Mojang) players and third-party (Yggdrasil / Blessing Skin) players join the same server through a single endpoint.

## Introduction

MCLoginProxy sits between your Minecraft server (with [authlib-injector](https://github.com/yushijinhun/authlib-injector)) and one or more upstream authentication services. When a client tries to join, the proxy queries each configured server in order — Mojang official auth and any number of Blessing Skin / Yggdrasil API servers — and returns the first successful profile. This allows premium and third-party accounts to coexist on the same server without forcing players to switch launchers or accounts.

## Features

- Aggregates Mojang official authentication and multiple Blessing Skin / Yggdrasil servers behind one endpoint
- Sequential failover across all configured authentication servers
- Automatic Mojang public-keys sync with local cache (Mojang → LittleSkin fallback, periodic refresh)
- HTTP / HTTPS upstream proxy support (optional basic auth)
- Per-server player blacklist (SQLite-backed, scoped by UUID + server)
- Interactive console (`ban` / `unban` / `reload` / `quit` / `exit` / `stop`)
- Hot configuration reload without restart
- Rotating file logs

## HTTP Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/` | Returns the Yggdrasil API meta document (`static/index.json`) |
| GET    | `/minecraftservices/publickeys` | Returns the cached Mojang public keys |
| GET    | `/sessionserver/session/minecraft/hasJoined` | Verifies a join attempt across all configured authentication servers |

## Deployment

### Docker (recommended)

Build the image from the project root:

```bash
docker build -t mcloginproxy .
```

Run the container:

```bash
docker run -d \
  --name mcloginproxy \
  -p 30000:30000 \
  -v $(pwd)/config.toml:/workspace/config.toml \
  -v $(pwd)/static:/workspace/static \
  -v $(pwd)/logs:/workspace/logs \
  mcloginproxy
```

Notes:

- On first launch, if `config.toml` is missing, a default one is generated. Stop the container, edit it, and restart.
- The container exposes port `30000` internally; change the host mapping (`-p <host>:30000`) as needed.
- Persist `static/` so that `accounts.db` (blacklist) and the cached `publickeys.json` survive container rebuilds.

### From source (for development)

```bash
git clone https://github.com/KasakiNova/MCLoginProxy
cd MCLoginProxy
python -m venv .venv
# Activate venv (OS specific)
pip install -r requirements.txt
python main.py
```

Requires Python 3.11+. Python 3.9 / 3.10 also works thanks to the `tomli` fallback pinned in `requirements.txt`.

## Configuration (`config.toml`)

Only **TOML** is currently supported. The file lives in the working directory and is created automatically on first run.

```toml
[General]
# Enable debug mode (false: info, true: debug)
debug = false
# Binding IP
ip = "127.0.0.1"
# Service listening port
port = 30000
# Public-keys refresh interval (seconds). 0 disables periodic refresh.
CheckKeysTime = 7200

[Log]
# Whether to save logs to disk
save-log = false
# Log directory
log_dir = "logs"
# Maximum number of rotated log files to keep
max_save_log = 5

[Proxy]
# Enable upstream HTTP/HTTPS proxy
enable = false
# Proxy address, protocol required (http / https)
address = "http://127.0.0.1:8080"
# Optional basic-auth for the proxy
enable_auth = false
username = ""
password = ""

# Authentication servers are evaluated in order: Server.0, Server.1, ...
# The first server that returns a valid profile wins.
# ServerType values:
#   - Mojang   : Mojang official session server
#   - Blessing : Blessing Skin / Yggdrasil-compatible API
[Server.0]
Name = "Mojang"
ServerType = "Mojang"
NeedProxy = false

[Server.1]
Name = "LittleSkin"
ServerType = "Blessing"
NeedProxy = false
Url = "https://littleskin.cn/api/yggdrasil"
```

### Configuring authentication servers

Authentication servers are declared as `[Server.N]` blocks, where `N` is a non-negative integer. The proxy tries them strictly in numeric order (`Server.0`, `Server.1`, `Server.2`, ...) and returns the first server that successfully verifies the player. You can declare as many servers as you need; put the most trusted or lowest-latency provider first.

Each block accepts the following fields:

| Field | Required | Description |
|-------|----------|-------------|
| `Name` | yes | Display name used in logs. |
| `ServerType` | yes | Either `Mojang` (Mojang official session server) or `Blessing` (Blessing Skin / Yggdrasil-compatible API). Case-insensitive. |
| `NeedProxy` | yes | `true` to route requests to this server through the upstream proxy defined in `[Proxy]`. Requires `[Proxy].enable = true` to actually take effect. |
| `Url` | only for `Blessing` | Root URL of the Yggdrasil API, e.g. `https://littleskin.cn/api/yggdrasil`. Do **not** include a trailing slash or the `/sessionserver/...` path — the proxy appends them automatically. |

**Example — Mojang first, then two Blessing Skin servers:**

```toml
[Server.0]
Name = "Mojang"
ServerType = "Mojang"
NeedProxy = true            # Route Mojang requests through [Proxy] if needed

[Server.1]
Name = "LittleSkin"
ServerType = "Blessing"
NeedProxy = false
Url = "https://littleskin.cn/api/yggdrasil"

[Server.2]
Name = "MCSkinComCn"
ServerType = "Blessing"
NeedProxy = false
Url = "https://mcskin.com.cn/api/yggdrasil"
```

Tips:

- The numeric suffix only determines order; the values themselves do not have to be contiguous, but keeping them sequential makes the config easier to read.
- A `Mojang` block does not need a `Url` field — the official endpoint is built in.
- If a server is unreachable or returns a non-200 response, the proxy logs the failure and falls through to the next server. Only when all servers fail will the join attempt be rejected.

## Console Commands

After the service starts, an interactive prompt is available on stdin.

| Command | Usage | Description |
|---------|-------|-------------|
| `ban`   | `ban <player_name> [index]` | Ban a player. Use `index` when multiple accounts share the same name. |
| `unban` | `unban <player_name> [index]` | Reverse of `ban`. |
| `reload` | `reload` | Reload `config.toml` without restarting the service. |
| `quit` / `exit` / `stop` | — | Shut down the service. |

When a name is ambiguous, the affected command prints a table of matching accounts so you can re-run it with the appropriate `index`.

## Integration with authlib-injector

[authlib-injector](https://github.com/yushijinhun/authlib-injector) is a Java agent loaded by the Minecraft **server** to redirect authentication to a custom Yggdrasil endpoint. Point it at MCLoginProxy and your server will accept both Mojang and the configured Blessing Skin / Yggdrasil accounts.

Server startup flag (Spigot / Paper / Forge / Fabric, etc.):

```bash
java -javaagent:authlib-injector.jar=http://<proxy-host>:30000 \
     -jar server.jar nogui
```

## Acknowledgements

- [authlib-injector](https://github.com/yushijinhun/authlib-injector) — the Java agent that makes custom Yggdrasil authentication possible on the Minecraft server side.

## License

Licensed under the [Apache License 2.0](LICENSE).
