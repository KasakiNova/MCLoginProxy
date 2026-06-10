# coding=utf-8
"""Interactive console for MCLoginProxy.

Provides ``ban`` / ``unban`` / ``reload`` / ``quit`` commands
via the Python ``cmd`` module.
"""
import cmd
import sys

from prettytable import PrettyTable

import modules.globalVariables as gVar
from modules.configs.config import Config
from modules.services.blacklistService import BlacklistService
from modules.utils.logger import info, error, warning, command_log, debug, setup_logger
from modules.utils.proxies import Proxies


def _quit_application() -> None:
    """Print shutdown message and exit."""
    print("\nShutting down...")
    print("Bye~")
    sys.exit(0)


def _get_server_name(server_id) -> str:
    """Return the human-readable server name for a given config key."""
    return gVar.cfgContext['Server'][str(server_id)]['Name']


class MainConsole(cmd.Cmd):
    """CLI console for the proxy server."""

    intro_message = (
        "Welcome to Minecraft Login Proxy!\n"
        "Created by KasakiNova\n"
        "Open-sourced under the Apache-2.0 license.\n"
        "GitHub Repository: https://github.com/KasakiNova/MCLoginProxy\n"
        "Type 'help' to list available commands."
    )
    intro = intro_message
    prompt = '--> '

    def __init__(self) -> None:
        super().__init__()
        self.blacklistService = BlacklistService()
        self.table = PrettyTable()

    def preloop(self) -> None:
        """Log console startup."""
        command_log(f"--> [Init] Console ready.\n{self.intro}")

    def precmd(self, line: str) -> str:
        """Log every command before execution."""
        if line.strip():
            command_log(f"--> {line}")
        return line

    def emptyline(self) -> None:
        """Do nothing on empty input (don't repeat last command)."""

    def default(self, line: str) -> None:
        """Handle unrecognized commands."""
        warning(f"Unknown command: {line}")

    def do_ban(self, args: str) -> None:
        """Ban a player: ban <player_name> [<index>]"""
        if not args:
            print("No arguments given, use: ban <player_name> [<index>]")
            return
        args_split = args.split(' ')
        name = args_split[0]
        index = None
        if len(args_split) > 1:
            try:
                index = int(args_split[1])
            except ValueError:
                print("Invalid index, use a number")
                return

        if index is not None:
            result = self.blacklistService.ban_by_index(name, index)
        else:
            result = self.blacklistService.ban(name)

        self._handle_result(result, "ban", name)

    def do_unban(self, args: str) -> None:
        """Unban a player: unban <player_name> [<index>]"""
        if not args:
            print("No arguments given, use: unban <player_name> [<index>]")
            return
        args_split = args.split(' ')
        name = args_split[0]
        index = None
        if len(args_split) > 1:
            try:
                index = int(args_split[1])
            except ValueError:
                print("Invalid index, use a number")
                return

        if index is not None:
            result = self.blacklistService.unban_by_index(name, index)
        else:
            result = self.blacklistService.unban(name)

        self._handle_result(result, "unban", name)

    def _handle_result(self, result: dict, action: str, name: str) -> None:
        """Display the outcome of a ban/unban command."""
        if result['msg'] == "Success":
            info(f"Successfully {action}ned player {name}")
        elif result['msg'] == "Already":
            warning(f"Player {name} has already been {action}ned")
        elif result['msg'] == "NotFound":
            warning(f"Unable to find {name}")
        elif result['msg'] == "IndexError":
            warning("Index out of range or invalid")
        elif result['msg'] == "Multiple":
            print(f"Found multiple accounts for player \"{name}\":")
            print(self._build_account_table(result['data']))
            print(
                f"Please specify an index, "
                f"use: {action} <player_name> <index>"
            )

    def _build_account_table(self, data: list) -> PrettyTable:
        """Render a PrettyTable for account lookup results."""
        self.table.clear_rows()
        self.table.field_names = ["Index", "Name", "Server", "UUID"]
        for i, row in enumerate(data, start=1):
            uuid, name, server_id, _ = row
            srv_name = _get_server_name(server_id)
            self.table.add_row([i, name, srv_name, uuid])
        return self.table

    def do_quit(self, _) -> None:
        """Quit Application"""
        _quit_application()

    def do_exit(self, _) -> None:
        """Exit Application"""
        _quit_application()

    def do_stop(self, _) -> None:
        """Stop Application"""
        _quit_application()

    def do_reload(self, _) -> None:
        """Reload config from config.toml"""
        try:
            cfg = Config()
            cfg.init()
            gVar.cfgContext = cfg.read()
            setup_logger(gVar.cfgContext, gVar.debugMode)
            Proxies()
            info("Config reloaded successfully")
            if gVar.debugMode:
                debug(f"Config: \n{gVar.cfgContext}")
                if gVar.cfgContext.get('Proxy', {}).get('enable', False):
                    debug(f"ProxiesLink: \n{gVar.proxies}")
        except Exception as e:
            error(f"Failed to reload config: {e}")
