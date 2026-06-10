# coding=utf-8
"""MCLoginProxy - Minecraft Yggdrasil authentication proxy server.

Routes Minecraft client ``hasJoined`` requests through configurable
authentication servers (Mojang official and third-party Blessing Skin
Yggdrasil APIs), with per-server blacklist support.

Usage: python main.py
"""
import logging
import sys
import threading
from time import sleep

from paste.translogger import TransLogger
from waitress import serve

import modules.globalVariables as gVar
from modules.configs.config import Config
from modules.console.mainConsole import MainConsole
from modules.services.defWebapp import WebApp
from modules.services.publickeys import PublicKeys
from modules.utils.logger import info, error, warning, debug as log_debug, setup_logger
from modules.utils.proxies import Proxies


def initialize_config() -> None:
    """Load and validate ``config.toml``; create default if missing."""
    cfg = Config()
    sleep(0.001)
    if cfg.init():
        gVar.cfgContext = cfg.read()
        setup_logger(gVar.cfgContext, gVar.debugMode)
        info("Config File Loaded")
    else:
        error("Please check your config and try again")
        sys.exit()


def initialize_services() -> None:
    """Initialize database migration, static files, publickeys, and proxy."""
    from modules.database.accountInfoDB import check_and_migrate_db

    if check_and_migrate_db():
        info("Database schema migrated (uuid → uuid+server composite key).")
        info("Please restart the application.")
        sys.exit(0)

    WebApp()

    publickeys = PublicKeys()
    publickeys.start_thread()

    proxies = Proxies()
    if gVar.proxies and not proxies.check_proxies():
        error("Proxy is incorrect")
        sys.exit()


def start_waitress(thread: int = 10) -> None:
    """Launch the Waitress WSGI server (blocking)."""
    from modules.webapp.httpLogic import app

    logger = logging.getLogger("waitress")
    logger.setLevel(logging.INFO)
    try:
        serve(
            TransLogger(app, setup_console_handler=False),
            host=gVar.cfgContext["General"]["ip"],
            port=gVar.cfgContext["General"]["port"],
            threads=thread,
            ident="YggdrasilProxyServer",
            channel_timeout=20,
            max_request_body_size=10 * 1024 * 1024
        )
    except PermissionError as e:
        if e.winerror == 10013:
            error(f"Port {gVar.cfgContext['General']['port']} is already in use.")
        error(f"Permission Error: {e}")
        sys.exit()
    except OSError as e:
        if e.errno == 98:
            error(f"Port {gVar.cfgContext['General']['port']} is already in use.")
        error(f"OS Error: {e}")
        sys.exit()


def run_wsgi_server() -> None:
    """Start the WSGI server (convenience wrapper)."""
    start_waitress()


def main() -> None:
    """Application entry point."""
    initialize_config()
    initialize_services()

    if gVar.debugMode:
        log_debug(f"Config: \n{gVar.cfgContext}")
        if gVar.cfgContext['Proxy']['enable']:
            log_debug(f"ProxiesLink: \n{gVar.proxies}")

    http_thread = threading.Thread(target=run_wsgi_server)
    http_thread.daemon = True
    http_thread.start()

    sleep(0.5)
    MainConsole().cmdloop()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        info("Shutting down...")
        info("Bye~")
