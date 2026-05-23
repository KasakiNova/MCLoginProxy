# coding=utf-8
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
    """Init Config"""
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
    """Init WebApp and PublicKeys"""
    # setup static dir and index.json
    WebApp()
    # try to init publickeys
    publickeys = PublicKeys()
    publickeys.start_thread()

    # Init Proxies Link
    proxies = Proxies()
    if gVar.proxies and not proxies.check_proxies():
        error("Proxy is incorrect")
        sys.exit()


def start_waitress(thread:int=10) -> None:
    """Start server with waitress"""
    from modules.webapp.httpLogic import app
    # Set waitress log level
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
        # # Maybe for Windows
        if e.winerror == 10013: # This error code 10013 for windows Port is in use
            error(f"Port {gVar.cfgContext['General']['port']} is already in use.")
        error(f"Permission Error: {e}")
        sys.exit()
    except OSError as e:
        # This error maybe for unix system, like Linux or macOS
        if e.errno == 98: # Error code 98 is port already use
            error(f"Port {gVar.cfgContext['General']['port']} is already in use.")
        error(f"OS Error: {e}")
        sys.exit()


# Start WSGI Server thread
def run_wsgi_server() -> None:
    start_waitress()


def main() -> None:
    """Main Service"""

    # init config and services
    initialize_config()
    initialize_services()

    # If debugMode is true, print all config
    if gVar.debugMode:
        log_debug(f"Config: \n{gVar.cfgContext}")
        if gVar.cfgContext['Proxy']['enable']:
            log_debug(f"ProxiesLink: \n{gVar.proxies}")

    # print System info
    # try:
    #     if not gVar.cfgContext["General"]["disableSysInfo"]:
    #         sysinfo()
    # except Exception:
    #     sysinfo()

    # Create a new thread to run http server
    http_thread = threading.Thread(target=run_wsgi_server)
    http_thread.daemon=True
    http_thread.start()

    # Running Console
    sleep(0.5)
    MainConsole().cmdloop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        info("Shutting down...")
        info("Bye~")
