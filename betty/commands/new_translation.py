from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final, override

from betty import gettext
from betty.app import App
from betty.argparse import validator_to_argument_type
from betty.asset import AssetDirectoryDefinition
from betty.console import Command, CommandDefinition
from betty.factory import Manufacturable
from betty.functools import Pipe
from betty.localizables.gettext import _
from betty.machine_name import MachineName
from betty.plugin.error import PluginNotFound
from betty.validators.locale import is_locale

if TYPE_CHECKING:
    import argparse
    from collections.abc import Mapping

    from babel import Locale

    from betty.console import CommandFunction


@final
@CommandDefinition("new-translation", label=_("Create a new translation"))
class NewTranslation(Manufacturable, Command):
    """
    .. plugin:: command:new-translation.
    """

    def __init__(self, app: App, /):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        assets: Mapping[MachineName, AssetDirectoryDefinition] = {
            asset.id: asset
            async for asset in self._app.plugins[AssetDirectoryDefinition]
        }

        def _assert_asset(asset_id: MachineName) -> AssetDirectoryDefinition:
            try:
                asset = assets[asset_id]
            except KeyError:
                raise PluginNotFound(
                    AssetDirectoryDefinition, asset_id, assets.keys()
                ) from None
            return asset

        parser.add_argument(
            "output",
            type=validator_to_argument_type(Pipe(MachineName) | _assert_asset),
        )
        parser.add_argument(
            "locale",
            type=validator_to_argument_type(is_locale),
        )
        return self._command_function

    async def _command_function(
        self, output: AssetDirectoryDefinition, locale: Locale
    ) -> None:
        await gettext.new_translation(output, locale, ui=self._app.ui)
