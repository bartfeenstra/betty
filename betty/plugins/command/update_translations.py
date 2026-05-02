from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final, override

from betty.app import App
from betty.argparse import assertion_to_argument_type
from betty.assertion import assert_directory
from betty.asset import AssetDirectoryDefinition
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.factory import Manufacturable
from betty.locale import translation
from betty.locale.localizable.gettext import _
from betty.plugin.error import PluginNotFound

if TYPE_CHECKING:
    import argparse
    from collections.abc import Mapping
    from pathlib import Path


@final
@CommandDefinition(
    "update-translations",
    label=_("Update existing translations"),
)
class UpdateTranslations(Manufacturable, Command):
    """
    .. plugin:: command:update-translations.
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
        localizer = await self._app.localizer
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
            type=assertion_to_argument_type(_assert_asset, localizer=localizer),
        )
        parser.add_argument(
            "inputs",
            type=assertion_to_argument_type(assert_directory(), localizer=localizer),
            nargs="+",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            type=assertion_to_argument_type(assert_directory(), localizer=localizer),
            default=[],
            dest="excludes",
        )
        return self._command_function

    async def _command_function(
        self,
        output: AssetDirectoryDefinition,
        inputs: tuple[Path],
        excludes: tuple[Path],
    ) -> None:
        await translation.update_translations(
            output.assets, inputs, excludes, user=self._app.user
        )
