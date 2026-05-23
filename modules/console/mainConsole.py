# coding=utf-8
import cmd
import sys

from prettytable import PrettyTable
import modules.globalVariables as gVar
from modules.configs.config import Config
from modules.services.blacklistService import BlacklistService
from modules.utils.logger import info, error, warning, command_log, debug, setup_logger


def _quit_application():
    """Quit Application"""
    print("\nShutting down...")
    print("Bye~")
    sys.exit(0)


def _get_server_name(server_id):
    return gVar.cfgContext['Server'][str(server_id)]['Name']


class MainConsole(cmd.Cmd):
    intro_message = (
        "Welcome to Minecraft Login Proxy!\n"
        "Created by KasakiNova\n"
        "Open-sourced under the Apache-2.0 license.\n"
        "GitHub Repository: https://github.com/KasakiNova/MCLoginProxy\n"
        "Type 'help' to list available commands."
    )
    intro = intro_message
    prompt = '--> '

    def __init__(self):
        super().__init__()
        self.has_new_data = False
        self.blacklistService = BlacklistService()
        self.table = PrettyTable()

    def preloop(self):
        command_log(f"--> [Init] Console ready.\n{self.intro}")

    def precmd(self, line):
        if line.strip():
            command_log(f"--> {line}")
        return line

    def do_ban(self, args):
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

        if result['msg'] == "Success":
            info(f"Successfully banned player {name}")
        elif result['msg'] == "Already":
            warning(f"Player {name} has been banned")
        elif result['msg'] == "NotFound":
            warning(f"Unable to find {name}")
        elif result['msg'] == "IndexError":
            warning(f"Index out of range or invalid")
        elif result['msg'] == "Multiple":
            print(f"Found multiple accounts for player \"{name}\":")
            print(self._build_account_table(result['data']))
            print("Please specify an index, use: ban <player_name> <index>")

    def do_unban(self, args):
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

        if result['msg'] == "Success":
            info(f"Successfully unbanned player {name}")
        elif result['msg'] == "Already":
            warning(f"Player {name} has not been banned")
        elif result['msg'] == "NotFound":
            warning(f"Unable to find {name}")
        elif result['msg'] == "IndexError":
            warning(f"Index out of range or invalid")
        elif result['msg'] == "Multiple":
            print(f"Found multiple accounts for player \"{name}\":")
            print(self._build_account_table(result['data']))
            print("Please specify an index, use: unban <player_name> <index>")

    def _build_account_table(self, data):
        self.table.clear_rows()
        self.table.field_names = ["Index", "Name", "Server", "UUID"]
        for i, row in enumerate(data, start=1):
            uuid, name, server_id, _ = row
            srv_name = _get_server_name(server_id)
            self.table.add_row([i, name, srv_name, uuid])
        return self.table


    def do_quit(self, _):
        """Quit Application"""
        _quit_application()

    def do_exit(self, _):
        """Exit Application"""
        _quit_application()

    def do_reload(self, _):
        """Reload config from config.toml"""
        try:
            cfg = Config()
            cfg.init()
            gVar.cfgContext = cfg.read()
            setup_logger(gVar.cfgContext, gVar.debugMode)
            info("Config reloaded successfully")
            if gVar.debugMode:
                debug(f"Config: \n{gVar.cfgContext}")
                if gVar.cfgContext.get('Proxy', {}).get('enable', False):
                    debug(f"ProxiesLink: \n{gVar.proxies}")
        except Exception as e:
            error(f"Failed to reload config: {e}")

    def do_stop(self, _):
        """Stop Application"""
        _quit_application()

    def emptyline(self):
        """Override the default behavior of repeating the last command on an empty line."""
        pass  # Do nothing

    def default(self, line):
        """Unknown Command"""
        warning(f"Unknown command: {line}")
