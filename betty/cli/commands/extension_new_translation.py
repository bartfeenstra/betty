from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self

import asyncclick as click
from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import assert_locale_identifier
from betty.cli.commands import command, parameter_callback, Command
from betty.locale import translation
from betty.locale.localizable import _
from betty.locale.translation import assert_extension_has_assets_directory_path
from betty.plugin import ShorthandPluginBase
from betty.project import extension

if TYPE_CHECKING:
    from betty.app import App
    from betty.project.extension import Extension


@final
class ExtensionNewTranslation(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to create new translations for an extension.
    """

    _plugin_id = "extension-new-translation"
    _plugin_label = _("Create a new translation for an extension")

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def click_command(self) -> click.Command:
        localizer = await self._app.localizer
        extension_id_to_type_map = await extension.EXTENSION_REPOSITORY.mapping()
        description = self.plugin_description()

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
                    extension_id_to_type_map.get(extension_id)
                )
            ),
        )
        @click.argument(
            "locale",
            required=True,
            callback=parameter_callback(assert_locale_identifier()),
        )
        async def extension_new_translation(  # noqa D103
            extension: type[Extension], locale: str
        ) -> None:
            await translation.new_extension_translation(locale, extension)

        return extension_new_translation
