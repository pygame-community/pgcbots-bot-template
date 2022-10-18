"""This file represents the main entry point into the bot application.
"""
import asyncio
import contextlib
import copy
import importlib.util
import logging
import os
import os.path
import sys
import types
from typing import Any, Optional

import click
import discord
from discord.ext import commands
import snakecore  # TODO: Remove this if not using snakecore

from .bot import (
    TemplateBot as Bot,
)  # TODO: Rename TemplateBot according to your bot application.

try:
    import uvloop  # type: ignore
except ImportError:
    pass
else:
    # uvloop replaces the default Python event loop with a cythonized version.
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

LOG_LEVEL_NAMES: set[str] = {
    "CRITICAL",
    "FATAL",
    "ERROR",
    "WARN",
    "WARNING",
    "INFO",
    "DEBUG",
    "NOTSET",
}


DEFAULT_EXTENSIONS: list[dict[str, Any]] = [
    # Add extensions here that should always be loaded upon startup.
    # These can only be excluded through the --ignore-ext' or '--disable-all-exts'
    # CLI options.
]


DEFAULT_CONFIG = {
    "intents": discord.Intents.default().value,
    "command_prefix": "!",
    "mention_as_command_prefix": False,
    "extensions": [
        {"name": f"{__package__}.exts.ping_pong"},  # TODO: Remove this extension entry
    ],
}

config: dict = copy.deepcopy(DEFAULT_CONFIG)


def import_module_from_path(module_name: str, file_path: str) -> types.ModuleType:
    abs_file_path = os.path.abspath(file_path)
    spec = importlib.util.spec_from_file_location(module_name, abs_file_path)
    if spec is None:
        raise ImportError(
            f"failed to generate module spec for module named '{module_name}' at '{abs_file_path}'"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)  # type: ignore
    except FileNotFoundError as fnf:
        raise ImportError(
            f"failed to find code for module named '{module_name}' at '{abs_file_path}'"
        ) from fnf
    return module


def setup_logging(log_level: int = logging.INFO) -> None:
    discord.utils.setup_logging(level=log_level)


def clear_logging_handlers(logger: Optional[logging.Logger] = None):
    if logger is None:
        logger = logging.getLogger()

    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)


@contextlib.contextmanager
def logging_handling(log_level: int = logging.INFO):
    try:
        setup_logging(log_level=log_level)
        yield
    finally:
        clear_logging_handlers()


async def start_bot(bot: Bot) -> None:
    try:
        await snakecore.init(
            global_client=bot
        )  # TODO: Remove this if not using snakecore
        print(f"\nStarting bot ({bot.__class__.__name__})...")
        await bot.start(bot._config["authentication"]["token"])
    except KeyboardInterrupt:
        pass
    finally:
        await close_bot(bot)


async def close_bot(bot: Bot) -> None:
    print("Closing bot...")
    await bot.close()
    await snakecore.quit()  # TODO: Remove this if not using snakecore


# fmt: off
@click.group(invoke_without_command=True, add_help_option=False)
@click.option("--config", "--config-path", "config_path", default="./config.py",
    show_default=True, type=click.Path(resolve_path=True),
    help="A path to the 'config.py' file to use for configuration. "
    "credentials and launching. Failure will occur silently for an "
    "invalid/non-existing path.")
@click.option("--localconfig", "--localconfig-path", "localconfig_path",
    default="./localconfig.py", show_default=True, type=click.Path(resolve_path=True),
    help="A path to the optional 'localconfig.py' file to use for locally overriding "
    "'config.py'. Failure will occur silently if this file could cannot be found/read "
    "successfully, except when 'config.py' is not provided, in which case an error "
    "will occur.")
@click.option("--intents", type=str,
    help=("The integer of bot intents as bitwise flags to be used by the bot instead "
    f"of discord.py's defaults ({bin(DEFAULT_CONFIG['intents'])}). "
    "It can be specified as a base 2, 8, 10 or 16 integer literal. Note that the "
    "message content intent (1 << 15) flag is not set by default. See more at "
    "https://discord.com/developers/docs/topics/gateway#list-of-intents"))
@click.option("--command-prefix", "--prefix", "command_prefix", multiple=True,
    show_default=True, type=str,
    help=("The command prefix(es) to use. "
    f"By default, {DEFAULT_CONFIG['command_prefix']} is used as a prefix."))
@click.option("--mention-as-command-prefix", "--mention-as-prefix",
    "mention_as_command_prefix", is_flag=True,
    help="Enable the usage of bot mentions as a prefix.")
@click.option("--ignore-ext", "--ignore-extension", "ignore_extension",
    multiple=True, type=str,
    help="The qualified name(s) of the extension(s) to ignore when loading extensions "
    "during startup.")
@click.option("--ignore-all-exts", "--ignore-all-extensions", "ignore_all_extensions",
    is_flag=True, help="Ignore all extensions at startup.")
@click.option("--ignore-default-exts", "--ignore-default-extensions",
    "ignore_default_extensions", is_flag=True, help="Ignore default extensions "
    "at startup.")
@click.option("--ignore-extra-exts", "--ignore-extra-extensions",
    "ignore_extra_extensions", is_flag=True,
    help="Ignore extra (non-default) extensions at startup.")
@click.option("--log-level", "--bot-log-level", "log_level",
    show_default=True, type=click.Choice(
        ('NOTSET', 'DEBUG', 'INFO', 'WARNING', 'WARN', 'ERROR', 'FATAL', 'CRITICAL'), case_sensitive=False),
    help="The log level to use for the bot's default logging system.")
# TODO: Add more CLI options specific to your application.
@click.help_option("-h", "--help", "help")
@click.pass_context
# fmt: on
def main(
    ctx: click.Context,
    config_path: Optional[str],
    localconfig_path: Optional[str],
    command_prefix: tuple[str, ...],
    mention_as_command_prefix: bool,
    intents: Optional[int],
    ignore_extension: tuple[str, ...],
    ignore_all_extensions: bool,
    ignore_default_extensions: bool,
    ignore_extra_extensions: bool,
    log_level: Optional[str],
):
    """Launch this Discord bot application."""

    if ctx.invoked_subcommand is not None:
        return

    click.echo("Searching for configuration files...")
    config_loading_failed = False

    if config_path:
        # load config data
        try:
            config_module = import_module_from_path("config", config_path)
            try:
                config.update(config_module.config)
            except AttributeError:
                click.secho(
                    "  Could not find 'config' data dictionary in 'config.py' "
                    f"file at '{config_path}'.",
                    err=True,
                    fg="red",
                )
                raise click.Abort()
            else:
                click.secho(f"  Successfully loaded 'config' data from {config_path}")
        except ImportError:
            if localconfig_path and os.path.exists(localconfig_path):
                click.secho(
                    f"  Could not find 'config.py' file at path '{config_path}', "
                    "looking for 'localconfig.py'...",
                    fg="yellow",
                )
            else:
                click.secho(
                    f"  Could not find 'config.py' file"
                    + (f" at '{config_path}'" if config_path else "")
                    + f" or 'localconfig.py' file at {localconfig_path}",
                    err=True,
                    fg="red",
                )
                raise click.Abort()

            config_loading_failed = True

    if localconfig_path:
        # load optional localconfig data
        try:
            localconfig_module = import_module_from_path(
                "localconfig", localconfig_path
            )
            try:
                config.update(localconfig_module.config)
            except AttributeError:
                click.secho(
                    "  Could not find the 'config' data dictionary in the "
                    f"'localconfig.py' file at '{localconfig_path}'.",
                    err=True,
                    fg="red",
                )
                raise click.Abort()
        except ImportError:
            if not config_path or config_loading_failed:
                click.secho(
                    f"  Could not find 'config.py' file"
                    + (f" at path '{config_path}'" if config_path else "")
                    + f" or 'localconfig.py' file at path {localconfig_path}",
                    err=True,
                    fg="red",
                )
                raise click.Abort()
            click.echo("  No 'localconfig.py' file found, continuing...")
        else:
            click.echo(f"  Successfully loaded 'localconfig' from {localconfig_path}")

    click.echo("Reading configuration data...")

    # -------------------------------------------------------------------------
    # config.authentication
    ## config.authentication.client_id
    ## config.authentication.token

    if (
        "authentication" not in config or not isinstance(config["authentication"], dict)
    ) or (
        "token" not in config["authentication"]
        or not isinstance(config["authentication"]["token"], str)
    ):
        click.secho(
            "  config error: 'authentication' variable must be of type 'dict' "
            "and must at least contain 'token' of type 'str'",
            err=True,
            fg="red",
        )
        raise click.Abort()

    # -------------------------------------------------------------------------
    # config.intents

    if intents is not None:
        config["intents"] = intents

    if not isinstance(config["intents"], int):
        intents_fail = False
        if isinstance(config["intents"], str):
            try:
                config["intents"] = int(
                    config["intents"],
                    base=(
                        2
                        if (base_hint := config["intents"][:2]) == "0b"
                        else 8
                        if base_hint == "0o"
                        else 16
                        if base_hint == "0x"
                        else 10
                    ),
                )
            except ValueError:
                intents_fail = True
        else:
            intents_fail = True

        if intents_fail:
            click.secho(
                "  config error: 'intents' variable must be of type 'int' or 'str' (STRING) "
                "and must be interpretable as an integer.",
                err=True,
                fg="red",
            )
            raise click.Abort()

    # -------------------------------------------------------------------------
    # config.command_prefix
    # config.mention_as_command_prefix

    final_prefix = None

    if command_prefix:
        config["command_prefix"] = command_prefix

    if (
        config["command_prefix"] is not None
        and not isinstance(config["command_prefix"], (str, list, tuple))
    ) or (
        isinstance(config["command_prefix"], (list, tuple))
        and not all(isinstance(pfx, str) for pfx in config["command_prefix"])
    ):
        click.secho(
            "  config error: Optional 'command_prefix' variable must be of type "
            "'str', of type 'list'/'tuple' containing strings or just None.",
            err=True,
            fg="red",
        )
        raise click.Abort()

    if mention_as_command_prefix:
        config["mention_as_command_prefix"] = mention_as_command_prefix

    if not isinstance(config["mention_as_command_prefix"], bool):
        click.secho(
            "  config error: 'mention_as_command_prefix' variable must be of type 'bool'.",
            err=True,
            fg="red",
        )
        raise click.Abort()

    if config["command_prefix"] is not None and config["mention_as_command_prefix"]:
        final_prefix = commands.when_mentioned_or(
            *(
                (config["command_prefix"],)
                if isinstance(config["command_prefix"], str)
                else config["command_prefix"]
            )
        )
    elif config["command_prefix"] is not None:
        final_prefix = config["command_prefix"]
    elif config["mention_as_command_prefix"]:
        final_prefix = commands.when_mentioned
    else:
        click.secho(
            "  config error: 'mention_as_command_prefix' variable must be True if 'command_prefix' is None.",
            err=True,
            fg="red",
        )
        raise click.Abort()

    # -------------------------------------------------------------------------
    # config.extensions

    if not isinstance(config["extensions"], (list, tuple)):
        click.secho(
            "  config error: 'exts' variable must be a container of type 'list'/'tuple' "
            "containing dictionaries that specify parameters for the extensions to load.",
            err=True,
            fg="red",
        )
        raise click.Abort()

    elif config["extensions"] and not all(
        isinstance(ext_dict, dict) and "name" in ext_dict
        for ext_dict in config["extensions"]
    ):
        click.secho(
            "  config error: The objects in the 'exts' variable container must be of type 'dict' "
            "and must at least contain the 'name' key mapping to the string name of an extension to load.",
            err=True,
            fg="red",
        )
        raise click.Abort()

    # -------------------------------------------------------------------------
    # config.log_level

    if "log_level" not in config:  # logging is disabled in the default configuration
        if log_level is not None:
            config["log_level"] = (log_level := log_level.upper())
        else:
            config["log_level"] = None

    elif config["log_level"] is not None and config["log_level"] not in LOG_LEVEL_NAMES:
        click.secho(
            "  config error: 'log_level' variable must be a valid log level name of type 'str' or None.",
            err=True,
            fg="red",
        )
        raise click.Abort()

    # -------------------------------------------------------------------------
    # TODO: Add support for more config variables as desired

    click.echo("  Finished reading configuration data")

    # handle extensions

    if ignore_all_extensions:
        config["extensions"] = []
    else:
        default_extensions = DEFAULT_EXTENSIONS
        extra_extensions = config["extensions"]
        final_extensions = []

        if not ignore_default_extensions:
            final_extensions.extend(default_extensions)
        if not ignore_extra_extensions:
            final_extensions.extend(extra_extensions)

        if ignore_extension:
            ignore_extension_set = set(ignore_extension)
            final_extensions = [
                ext_dict
                for ext_dict in final_extensions
                if ext_dict["name"] not in ignore_extension_set
            ]

        config["extensions"] = final_extensions

    # pass configuration data to bot instance
    bot = Bot(final_prefix, intents=discord.Intents(config["intents"]))  # type: ignore

    bot._config = config

    if (
        config["log_level"] is not None
    ):  #  not specifying a logging level disables logging
        with logging_handling(log_level=logging.getLevelName(config["log_level"])):
            asyncio.run(start_bot(bot))
            return

    asyncio.run(start_bot(bot))


if __name__ == "__main__":
    main()
