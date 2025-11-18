from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import assert_or, assert_none, assert_directory_path
from betty.console.assertion import assertion_to_argument_type
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.locale.localizable import _
from betty.locale.translation.project import extension as extension_translation
from betty.locale.translation.project.extension import (
    assert_extension_has_assets_directory_path,
)
from betty.project.extension import ExtensionDefinition

if TYPE_CHECKING:
    import argparse
    from pathlib import Path

    from betty.app import App


@final
@CommandDefinition(
    id="extension-update-translations",
    label=_("Update all existing translations for an extension"),
)
class ExtensionUpdateTranslations(AppDependentFactory, Command):
    """
    A command to update all of an extension's translations.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        extensions = await self._app.plugins(ExtensionDefinition)
        localizer = await self._app.localizer

        parser.add_argument(
            "extension",
            type=assertion_to_argument_type(
                lambda extension_id: assert_extension_has_assets_directory_path(
                    extensions[extension_id]
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
        self, extension: ExtensionDefinition, source: Path, exclude: tuple[Path] | None
    ) -> None:
        await extension_translation.update_extension_translations(
            extension, source, None if exclude is None else set(exclude)
        )
