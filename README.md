# Bot
A template repository that defines the structure for current and future Python bot projects using `discord.py`.
For ease of use, a CLI has been provided to customize bot startup and functioning. Supports Python `3.9+`. 

## Setup
1. Set up a virtual environment using your desired tool (e.g. `virtualenv`, `venv`, etc.).
2. Install requirements: `python -m pip install -U -r requirements.txt`.
3. Create all necessary [configuration](#configuration) files.
4. Launch the application via the [CLI](#cli) using `python -m bot` with any needed extra CLI options.

## Customization
All areas of code marked with `# TODO: ...` are meant to be looked at and potentially modified for a new project (e.g. renaming `TemplateBot` and `Bot-Author` in [`bot/__init__.py`](./bot/__init__.py), [`bot/__main__.py`](./bot/__main__.py) and [`bot/bot.py`](./bot/bot.py)), the rest of the repository and files can be extended as needed. Note however that some modifications may break the CLI, which would require making some changes to it as well.

## Configuration
Two files called `botconfig.py` and `launchconfig.py` should be used to provide information required for the bot to run. These files are meant to be stored locally on host machines without being 'added' to a Git repository. However, this suggestion may be ignored for workflows that don't permit it, and in such cases the files should be removed from the [`.gitignore`](./.gitignore) file. These files can either be stored in
the top level directory or somewhere else if custom paths are passed to the CLI.

If having separate configuration files is not desirable, a single `config.py` file can be used to contain the data of both `botconfig.py` and `launchconfig.py` instead.


### `botconfig.py`
This file is meant to hold the configuration settings, credentials and API endpoints of the bot application. Creating this file is mandatory and all data must be stored within a dictionary called `botconfig`. `"client_id"` and `"token"` are meant to be mandatory, whilst others are fully up to the implementation. For projects that use hosting solutions based on ephemeral file systems, credentials stored within the `"authentication"` dictionary like `"client_id"` and `"token"` can be turned into uppercase environment variables prefixed with `AUTH_` (e.g. `AUTH_CLIENT_ID` and `AUTH_TOKEN`) instead. The `botconfig.py` (excluding credentials and sensitive information) file can then be added to the project's Git repository to preserve it in those cases. As this file is a Python file, those credentials can be loaded into the `botconfig` dictionary during startup.

When loaded, bot applications should only need to parse the `botconfig` dictionary within the file.

#### Example code for ` botconfig.py` 
```py
botconfig = {
    "authentication": {
        "client_id": 1234567891011121314,
        "token": "...",
        "...": ...
    },
    "databases": {
        "a_database": {
            "engine": "sqlite",
            "library": "aiosqlite",
            "uri": "file:///path/to/a_database.db",
            "connection_arguments": {},  # arguments to pass to aiosqlite.connect() (DB-API 2.0)
        },
        {"...": ...} # other databases
    },
    "intents": 0b1100011111111011111101 # https://discord.com/developers/docs/topics/gateway#list-of-intents
}
```

### `launchconfig.py`
This file is meant to customize the launching/startup process of the bot application. Creating this file is optional but recommended. All data must be stored within a dictionary called `launchconfig`. 

For the dictionaries within the `"extensions"` list, the `"name"` and `"package"` keys match the names of the `name` and `package` arguments in the [`discord.ext.commands.Bot.load_extension`](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.Bot.load_extension) method and the values are meant to be forwarded to it, during startup. `"config"` (only supported with `snakecore`) can be used as a way to provide keyword arguments to extensions while they load, if supported. 

Depending on the desired workflow, this file may also be added to the Git repository of a bot project.

When loaded, bot applications should only need to parse the `launchconfig` dictionary within the file.

#### Example code for `launchconfig.py` 
```py
launchconfig = {
    "command_prefix": "!",  # can also be a list of prefixes
    "mention_as_command_prefix": True, # whether mentions may count as command prefixes
    "log_level": "INFO", # omission disables logging entirely
    "extensions": [
        {
            "name": "bot.exts.local_extension",
            "package": "bot",
            "config": {
                "a": 1,
                "b": 2
            }
        },
        # comment out extensions to disable them or use the `--ignore-extension ext_name` option via the CLI.
        # {
        #     "name": ".exts.local_extension2",
        #     "package": "bot"
        # },
        {
            "name": "global_extension" # globally installed Python packages can be loaded as extensions
        }
    ],
}
```


## CLI
The CLI is used to launch the bot application, whilst also allowing for selective overriding of config specified inside `config.py` or `botconfig.py` and `launchconfig.py` using command line options.
For some simple bot applications without extensions, the CLI can be used to fully replace `launchconfig.py` files.

```
Usage: python -m bot [OPTIONS]

  Launch this Discord bot application.

Options:
  --config, --config-path PATH    A path to the 'config.py' file to use for
                                  both configuring bot credentials and
                                  launching. This is resolved before '--
                                  botconfig-path' and '--launchconfig-path'.
                                  Failure will occur silently for an
                                  invalid/non-existing path.  [default:
                                  ./config.py]
  --botconfig, --botconfig-path PATH
                                  A path to the 'botconfig.py' file to use for
                                  configuring bot credentials.  [default:
                                  ./botconfig.py]
  --launchconfig, --launchconfig-path PATH
                                  A path to the 'launchconfig.py' file to use
                                  for configuring bot launching.  [default:
                                  ./launchconfig.py]
  --intents TEXT                  The integer of bot intents as bitwise flags
                                  to be used by the bot instead of
                                  discord.py's defaults
                                  (0b1100010111111011111101). It can be
                                  specified as a base 2, 8, 10 or 16 integer
                                  literal. Note that the message content
                                  intent (1 << 15) flag is not set by default.
                                  See more at https://discord.com/developers/d
                                  ocs/topics/gateway#list-of-intents
  --command-prefix, --prefix TEXT
                                  The command prefix(es) to use. By default, !
                                  is used as a prefix.
  --mention-as-command-prefix, --mention-as-prefix
                                  Enable the usage of bot mentions as a
                                  prefix.
  --ignore-ext, --ignore-extension TEXT
                                  The qualified name(s) of the extension(s) to
                                  ignore when loading extensions during
                                  startup.
  --ignore-all-exts, --ignore-all-extensions
                                  Ignore all extensions at startup.
  --ignore-default-exts, --ignore-default-extensions
                                  Ignore default extensions at startup.
  --ignore-extra-exts, --ignore-extra-extensions
                                  Ignore extra (non-default) extensions at
                                  startup.
  --log-level, --bot-log-level [NOTSET|DEBUG|INFO|WARNING|WARN|ERROR|FATAL|CRITICAL]
                                  The log level to use for the bot's default
                                  logging system.
  -h, --help                      Show this message and exit.
```
