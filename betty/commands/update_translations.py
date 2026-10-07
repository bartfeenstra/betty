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
from betty.validators.path import is_directory

if TYPE_CHECKING:
    import argparse
    from collections.abc import Mapping
    from pathlib import Path

    from betty.console import CommandFunction


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
            "inputs",
            type=validator_to_argument_type(is_directory),
            nargs="+",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            type=validator_to_argument_type(is_directory),
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
        await gettext.update_translations(
            output.assets, inputs, excludes, ui=self._app.ui
        )
