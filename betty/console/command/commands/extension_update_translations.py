from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.argparse import assertion_to_argument_type
from betty.assertion import assert_directory_path, assert_none, assert_or
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.extension import ExtensionDefinition
from betty.locale.localizable.gettext import _
from betty.locale.translation.project import extension as translation_project_extension
from betty.locale.translation.project.extension import (
    assert_extension_has_assets_directory_path,
)
from betty.service.factory import Manufacturable
from betty.service.requirement.app import require_app

if TYPE_CHECKING:
    import argparse
    from pathlib import Path

    from betty.app import App


@final
@CommandDefinition(
    "extension-update-translations",
    label=_("Update all existing translations for an extension"),
)
class ExtensionUpdateTranslations(Manufacturable, Command):
    """
    .. plugin:: command:extension-update-translations.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require_app
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        extensions = self._app.plugin.plugins(ExtensionDefinition)
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
                assert_or(assert_none, assert_directory_path()), localizer=localizer
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
        await translation_project_extension.update_extension_translations(
            extension, source, None if exclude is None else set(exclude)
        )
