from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import assert_locale_identifier
from betty.console.assertion import assertion_to_argument_type
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.locale import translation
from betty.locale.localizable import _
from betty.locale.translation.project import extension as extension_translation
from betty.project.extension import ExtensionDefinition

if TYPE_CHECKING:
    import argparse

    from betty.app import App


@final
@CommandDefinition(
    id="extension-new-translation",
    label=_("Create a new translation for an extension"),
)
class ExtensionNewTranslation(AppDependentFactory, Command):
    """
    A command to create new translations for an extension.
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
                lambda extension_id: translation.project.extension.assert_extension_has_assets_directory_path(
                    extensions[extension_id]
                ),
                localizer=localizer,
            ),
        )
        parser.add_argument(
            "locale",
            type=assertion_to_argument_type(
                assert_locale_identifier(), localizer=localizer
            ),
        )
        return self._command_function

    async def _command_function(
        self, extension: ExtensionDefinition, locale: str
    ) -> None:
        await extension_translation.new_extension_translation(
            locale, extension, user=self._app.user
        )
