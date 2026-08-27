from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final, override

from betty import gettext
from betty.app import App
from betty.argparse import assertion_to_argument_type
from betty.assertions.locale import assert_locale
from betty.asset import AssetDirectoryDefinition
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.factory import Arg1Manufacturable
from betty.localizables.gettext import _
from betty.plugin.error import PluginNotFound

if TYPE_CHECKING:
    import argparse
    from collections.abc import Mapping

    from babel import Locale


@final
@CommandDefinition("new-translation", label=_("Create a new translation"))
class NewTranslation(Arg1Manufacturable[App], Command):
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
        assets: Mapping[str, AssetDirectoryDefinition] = {
            asset.id: asset
            async for asset in self._app.plugins[AssetDirectoryDefinition]
        }

        def _assert_asset(asset_id: str) -> AssetDirectoryDefinition:
            try:
                asset = assets[asset_id]
            except KeyError:
                raise PluginNotFound(
                    AssetDirectoryDefinition, asset_id, assets.keys()
                ) from None
            return asset

        parser.add_argument(
            "output",
            type=assertion_to_argument_type(
                _assert_asset, localizer=self._app.user.localizer
            ),
        )
        parser.add_argument(
            "locale",
            type=assertion_to_argument_type(
                assert_locale(), localizer=self._app.user.localizer
            ),
        )
        return self._command_function

    async def _command_function(
        self, output: AssetDirectoryDefinition, locale: Locale
    ) -> None:
        await gettext.new_translation(output, locale, user=self._app.user)
