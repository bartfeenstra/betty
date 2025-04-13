from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

import asyncclick as click
from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import (
    assert_or,
    assert_none,
    assert_directory_path,
    assert_sequence,
)
from betty.cli.commands import command, Command, parameter_callback
from betty.locale import translation
from betty.locale.localizable import _
from betty.locale.translation import assert_extension_has_assets_directory_path
from betty.plugin import ShorthandPluginBase
from betty.project import extension

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App
    from betty.project.extension import Extension


@final
class ExtensionUpdateTranslations(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to update all of an extension's translations.
    """

    _plugin_id = "extension-update-translations"
    _plugin_label = _("Update all existing translations for an extension")

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def click_command(self) -> click.Command:
        localizer = await self._app.localizer
        description = self.plugin_description()
        extension_id_to_type_mapping = await extension.EXTENSION_REPOSITORY.mapping()

        @command(
            self.plugin_id(),
            short_help=self.plugin_label().localize(localizer),
            help=description.localize(localizer)
            if description
            else self.plugin_label().localize(localizer),
        )
        @click.argument(
            "extension",
            required=True,
            callback=parameter_callback(
                lambda extension_id: assert_extension_has_assets_directory_path(
                    extension_id_to_type_mapping.get(extension_id)
                )
            ),
        )
        @click.argument(
            "source",
            required=True,
            callback=parameter_callback(
                assert_or(assert_none(), assert_directory_path())
            ),
        )
        @click.option(
            "--exclude",
            multiple=True,
            callback=parameter_callback(assert_sequence(assert_directory_path())),
        )
        async def extension_update_translations(
            extension: type[Extension], source: Path, exclude: tuple[Path]
        ) -> None:
            await translation.update_extension_translations(
                extension, source, set(exclude)
            )

        return extension_update_translations
