from __future__ import annotations  # noqa: D100

from typing import TYPE_CHECKING, Self, final

from typing_extensions import override

from betty.argparse import assertion_to_argument_type
from betty.assertion import assert_locale
from betty.console.command import Command, CommandDefinition, CommandFunction
from betty.extension import ExtensionDefinition
from betty.locale.localizable.gettext import _
from betty.locale.translation.project import extension as extension_translation
from betty.locale.translation.project import extension as translation_project_extension
from betty.service.level.factory import ServiceLevelDependentSelfFactory
from betty.service.requirement.app import require_app

if TYPE_CHECKING:
    import argparse

    from babel import Locale

    from betty.app import App


@final
@CommandDefinition(
    "extension-new-translation", label=_("Create a new translation for an extension")
)
class ExtensionNewTranslation(ServiceLevelDependentSelfFactory, Command):
    """
    .. plugin:: command:extension-new-translation.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    @require_app
    async def new_for_services(cls, *, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        extensions = await self._app.plugins(ExtensionDefinition)
        localizer = await self._app.localizer
        parser.add_argument(
            "extension",
            type=assertion_to_argument_type(
                lambda extension_id: translation_project_extension.assert_extension_has_assets_directory_path(
                    extensions[extension_id]
                ),
                localizer=localizer,
            ),
        )
        parser.add_argument(
            "locale",
            type=assertion_to_argument_type(assert_locale(), localizer=localizer),
        )
        return self._command_function

    async def _command_function(
        self, extension: ExtensionDefinition, locale: Locale
    ) -> None:
        await extension_translation.new_extension_translation(
            locale, extension, user=self._app.user
        )
