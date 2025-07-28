from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import (
    assert_or,
    assert_none,
    assert_directory_path,
)
from betty.console.assertion import assertion_to_argument_type
from betty.console.command import Command, CommandFunction
from betty.locale import translation
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase

from betty.project import extension

if TYPE_CHECKING:
    import argparse
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
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        localizer = await self._app.localizer
        extension_id_to_type_mapping = await extension.EXTENSION_REPOSITORY.mapping()

        parser.add_argument(
            "extension",
            type=assertion_to_argument_type(
                lambda extension_id: translation.project.extension.assert_extension_has_assets_directory_path(
                    extension_id_to_type_mapping.get(extension_id)
                ),
                localizer=localizer,
            ),
        )
        parser.add_argument(
            "source",
            type=assertion_to_argument_type(
                assert_or(assert_none(), assert_directory_path()), localizer=localizer
            ),
        )
        parser.add_argument(
            "--exclude",
            action="append",
            type=assertion_to_argument_type(
                assert_directory_path(), localizer=localizer
            ),
        )
        return self._command_function

    async def _command_function(
        self, extension: type[Extension], source: Path, exclude: tuple[Path] | None
    ) -> None:
        await translation.project.extension.update_extension_translations(
            extension, source, None if exclude is None else set(exclude)
        )
