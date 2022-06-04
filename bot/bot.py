"""This file should define the `discord.ext.commands.Bot` subclass to use for the project. 
"""

import asyncio
import logging
from typing import Optional

from discord.ext import commands
import snakecore  # TODO: Remove this if not using snakecore


_logger = logging.getLogger(__name__)

# TODO: Rename TemplateBot according to your bot application.
# TODO: Replace snakecore.commands.Bot with `commands.Bot` if snakecore should not be used.
class TemplateBot(snakecore.commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.botconfig: dict = {}
        self.launchconfig: dict = {}
        self._setup_hook_task: Optional[asyncio.Task[None]] = None

    async def setup_hook(self) -> None:
        self._setup_hook_task = asyncio.create_task(self._setup_hook())

    async def _setup_hook(self) -> None:
        """Helper method to circumvent potential deadlocks for extensions whilst awaiting
        ``wait_until_ready()``.
        """
        await self.wait_until_ready()
        for ext_dict in self.launchconfig["extensions"]:
            try:
                await self.load_extension_with_config(
                    # TODO: Rename this to `load_extension` if not using snakecore
                    ext_dict["name"],
                    package=ext_dict.get("package"),
                    config=ext_dict.get("config"),
                    # TODO: Remove the `config=` argument above if not using snakecore
                )
            except (TypeError, commands.ExtensionFailed) as exc:
                _logger.error(
                    f"Failed to load extension '{ext_dict.get('package', '')}{ext_dict['name']}' at launch",
                    exc_info=exc,
                )
            except commands.ExtensionAlreadyLoaded:
                continue
            else:
                _logger.info(
                    f"Successfully loaded extension '{ext_dict.get('package', '')}{ext_dict['name']}' at launch"
                )
