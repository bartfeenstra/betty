from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.argparse import assertion_to_argument_type
from betty.assertion import assert_locale
from betty.asset import AssetDefinition
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.locale import translation
from betty.locale.localizable.gettext import _
from betty.plugin.error import PluginNotFound
from betty.requirement import require
from betty.service.factory import Manufacturable

if TYPE_CHECKING:
    import argparse

    from babel import Locale


@final
@CommandDefinition("new-translation", label=_("Create a new translation"))
class NewTranslation(Manufacturable, Command):
    """
    .. plugin:: command:new-translation.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require(App)
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        localizer = await self._app.localizer
        assets = {asset.id: asset async for asset in self._app.plugins[AssetDefinition]}

        def _assert_asset(asset_id: str) -> AssetDefinition:
            try:
                asset = assets[asset_id]
            except KeyError:
                raise PluginNotFound(AssetDefinition, asset_id, assets.keys()) from None
            return asset

        parser.add_argument(
            "output",
            type=assertion_to_argument_type(_assert_asset, localizer=localizer),
        )
        parser.add_argument(
            "locale",
            type=assertion_to_argument_type(assert_locale(), localizer=localizer),
        )
        return self._command_function

    async def _command_function(self, output: AssetDefinition, locale: Locale) -> None:
        await translation.new_translation(output, locale, user=self._app.user)
