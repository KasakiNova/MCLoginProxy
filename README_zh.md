# MCLoginProxy

[English](README.md) | [简体中文](README_zh.md)

一个 Minecraft Java 版的 Yggdrasil 认证代理服务，让正版（Mojang）玩家和外置登录（Yggdrasil / Blessing Skin）玩家可以通过同一个端点进入同一台服务器。

## 简介

MCLoginProxy 位于 Minecraft 服务端（搭配 [authlib-injector](https://github.com/yushijinhun/authlib-injector)）与一个或多个上游认证服务之间。当客户端尝试加入时，本代理会按配置顺序依次查询每个认证服务器——Mojang 官方认证以及任意数量的 Blessing Skin / Yggdrasil API 服务器，并返回第一个成功获取到的玩家档案。这样一来，正版与外置账户可以同时存在于同一台服务器，玩家也不需要切换启动器或账号。

## 特性

- 在单一端点后聚合 Mojang 官方认证与多个 Blessing Skin / Yggdrasil 服务器
- 已配置的认证服务器之间按顺序依次故障转移
- Mojang 公钥自动同步与本地缓存（Mojang → LittleSkin 回退，支持周期性刷新）
- 支持 HTTP / HTTPS 上游代理（可选基本认证）
- 玩家黑名单（基于 SQLite，按 UUID + 服务器维度记录）
- 交互式控制台（`ban` / `unban` / `reload` / `quit` / `exit` / `stop`）
- 配置热重载，无需重启
- 日志文件按数量轮转

## HTTP 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/` | 返回 Yggdrasil API 元信息文档（`static/index.json`） |
| GET  | `/minecraftservices/publickeys` | 返回已缓存的 Mojang 公钥 |
| GET  | `/sessionserver/session/minecraft/hasJoined` | 在所有已配置的认证服务器上验证玩家加入请求 |

## 部署

### Docker（推荐）

在项目根目录下构建镜像：

```bash
docker build -t mcloginproxy .
```

运行容器：

```bash
docker run -d \
  --name mcloginproxy \
  -p 30000:30000 \
  -v $(pwd)/config.toml:/workspace/config.toml \
  -v $(pwd)/static:/workspace/static \
  -v $(pwd)/logs:/workspace/logs \
  mcloginproxy
```

注意事项：

- 首次启动时如果 `config.toml` 不存在，会自动生成一份默认配置。请先停止容器，修改配置文件后再重新启动。
- 镜像内部暴露端口为 `30000`，宿主端口映射（`-p <host>:30000`）可按需修改。
- 建议持久化 `static/` 目录，使 `accounts.db`（黑名单）和缓存的 `publickeys.json` 能在重建容器后保留。

### 从源码运行（用于开发）

```bash
git clone https://github.com/KasakiNova/MCLoginProxy
cd MCLoginProxy
python -m venv .venv
# 激活 venv（视操作系统而定）
pip install -r requirements.txt
python main.py
```

需要 Python 3.11+。`requirements.txt` 中固定了 `tomli` 作为回退，因此 Python 3.9 / 3.10 也能运行。

## 配置文件（`config.toml`）

当前仅支持 **TOML** 格式。该文件位于工作目录，首次运行时会自动创建。

```toml
[General]
# 调试模式开关（false: info，true: debug）
debug = false
# 监听 IP
ip = "127.0.0.1"
# 服务监听端口
port = 30000
# 公钥刷新周期（秒），0 表示禁用周期性刷新
CheckKeysTime = 7200

[Log]
# 是否保存日志到文件
save-log = false
# 日志目录
log_dir = "logs"
# 最多保留的轮转日志文件数量
max_save_log = 5

[Proxy]
# 启用上游 HTTP/HTTPS 代理
enable = false
# 代理地址，必须带协议（http / https）
address = "http://127.0.0.1:8080"
# 代理基本认证（可选）
enable_auth = false
username = ""
password = ""

# 认证服务器按 Server.0、Server.1…… 的顺序依次尝试
# 第一个成功返回有效档案的服务器即被采用
# ServerType 取值：
#   - Mojang   ：Mojang 官方 session 服务器
#   - Blessing ：Blessing Skin / Yggdrasil 兼容 API
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

### 配置认证服务器

认证服务器以 `[Server.N]` 配置块声明，其中 `N` 是一个非负整数。本代理会严格按数字顺序（`Server.0`、`Server.1`、`Server.2`……）依次尝试，并采用第一个成功完成校验的服务器。你可以声明任意数量的服务器，建议把最可信、延迟最低的提供方放在最前面。

每个配置块支持以下字段：

| 字段 | 是否必填 | 说明 |
|------|----------|------|
| `Name` | 是 | 显示名称，用于日志输出。 |
| `ServerType` | 是 | 取值为 `Mojang`（Mojang 官方 session 服务器）或 `Blessing`（Blessing Skin / Yggdrasil 兼容 API），不区分大小写。 |
| `NeedProxy` | 是 | 为 `true` 时，该服务器的请求会走 `[Proxy]` 中定义的上游代理；同时需要 `[Proxy].enable = true` 才会真正生效。 |
| `Url` | 仅 `Blessing` 需要 | Yggdrasil API 的根地址，例如 `https://littleskin.cn/api/yggdrasil`。**不要**包含结尾的斜杠或 `/sessionserver/...` 路径——代理会自动补全。 |

**示例 —— 先 Mojang，再两个 Blessing Skin 服务器：**

```toml
[Server.0]
Name = "Mojang"
ServerType = "Mojang"
NeedProxy = true            # 如有需要，让 Mojang 请求走 [Proxy]

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

提示：

- 数字后缀只决定顺序；序号本身不要求连续，但建议保持连续以便阅读。
- `Mojang` 类型的配置块不需要 `Url` 字段——官方地址已内置。
- 当某个服务器不可达或返回非 200 响应时，代理会记录错误并继续尝试下一个服务器。只有所有服务器都失败时，加入请求才会被拒绝。

## 控制台命令

服务启动后会在标准输入提供一个交互式命令行。

| 命令 | 用法 | 说明 |
|------|------|------|
| `ban`   | `ban <玩家名> [index]` | 封禁玩家。当多个账号同名时，使用 `index` 指定。 |
| `unban` | `unban <玩家名> [index]` | `ban` 的反向操作。 |
| `reload` | `reload` | 不重启服务直接重新加载 `config.toml`。 |
| `quit` / `exit` / `stop` | — | 关闭服务。 |

当玩家名出现多重匹配时，对应命令会打印一张候选账号表，方便你带 `index` 重新执行。

## 与 authlib-injector 集成

[authlib-injector](https://github.com/yushijinhun/authlib-injector) 是一个由 Minecraft **服务端**加载的 Java agent，用来将认证请求重定向到自定义的 Yggdrasil 端点。把它指向 MCLoginProxy，服务端就能同时接受 Mojang 与已配置的 Blessing Skin / Yggdrasil 账号登录。

服务端启动参数（Spigot / Paper / Forge / Fabric 等）：

```bash
java -javaagent:authlib-injector.jar=http://<代理地址>:30000 \
     -jar server.jar nogui
```

## 致谢

- [authlib-injector](https://github.com/yushijinhun/authlib-injector) —— 让 Minecraft 服务端可以使用自定义 Yggdrasil 认证的 Java agent。

## 许可证

基于 [Apache License 2.0](LICENSE) 开源。
