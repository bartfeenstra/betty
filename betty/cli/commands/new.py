from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self, Any
from urllib.parse import urlparse

import asyncclick as click
from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.assertion import assert_str, assert_path, assert_locale
from betty.cli.commands import command, Command
from betty.cli.error import user_facing_error_to_bad_parameter
from betty.config import write_configuration_file
from betty.locale import get_display_name, DEFAULT_LOCALE
from betty.locale.localizable import _, StaticTranslations
from betty.machine_name import machinify, assert_machine_name
from betty.plugin import ShorthandPluginBase
from betty.plugin.config import PluginInstanceConfiguration
from betty.project.config import LocaleConfiguration, ProjectConfiguration
from betty.project.extension.deriver import Deriver
from betty.project.extension.gramps import Gramps
from betty.project.extension.gramps.config import (
    FamilyTreeConfiguration,
    GrampsConfiguration,
)
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.extension.maps import Maps
from betty.project.extension.privatizer import Privatizer
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.trees import Trees
from betty.project.extension.webpack import Webpack
from betty.project.extension.wikipedia import Wikipedia

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from betty.app import App


@final
class New(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to create a new project.
    """

    _plugin_id = "new"
    _plugin_label = _("Create a new project")

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

        @command(
            self.plugin_id(),
            short_help=self.plugin_label().localize(localizer),
            help=description.localize(localizer)
            if description
            else self.plugin_label().localize(localizer),
        )
        async def new() -> None:
            configuration_file_path = await click.prompt(
                localizer._(
                    "Where do you want to save your project's configuration file?"
                ),
                value_proc=user_facing_error_to_bad_parameter(localizer)(
                    _assert_project_configuration_file_path
                ),
            )
            configuration = await ProjectConfiguration.new(
                configuration_file_path,
            )

            configuration.extensions.enable(
                Deriver, Privatizer, RaspberryMint, Wikipedia
            )
            webpack_requirement = await Webpack.requirement()
            if webpack_requirement.is_met():
                configuration.extensions.enable(HttpApiDoc, Maps, Trees)

            configuration.locales.replace(
                LocaleConfiguration(
                    await click.prompt(
                        localizer._(
                            "Which language should your project site be generated in? Enter an IETF BCP 47 language code."
                        ),
                        default=DEFAULT_LOCALE,
                        value_proc=user_facing_error_to_bad_parameter(localizer)(
                            assert_locale()
                        ),
                    )
                )
            )
            while click.confirm(localizer._("Do you want to add another locale?")):
                configuration.locales.append(
                    LocaleConfiguration(
                        await click.prompt(
                            localizer._(
                                "Which language should your project site be generated in? Enter an IETF BCP 47 language code."
                            ),
                            value_proc=user_facing_error_to_bad_parameter(localizer)(
                                assert_locale()
                            ),
                        )
                    )
                )
            locales = list(configuration.locales)

            configuration.title = await _prompt_static_translations(
                locales,
                localizer._("What is your project called in {locale}?"),
            )

            configuration.name = await click.prompt(
                localizer._("What is your project's machine name?"),
                default=machinify(
                    configuration.title.localize(
                        await self._app.localizers.get(
                            configuration.locales.default.locale
                        )
                    )
                ),
                value_proc=user_facing_error_to_bad_parameter(localizer)(
                    assert_machine_name()
                ),
            )

            configuration.author = await _prompt_static_translations(
                locales,
                localizer._("What is the project author called in {locale}?"),
            )

            configuration.url = await click.prompt(
                localizer._("At which URL will your site be published?"),
                default="https://example.com",
                value_proc=user_facing_error_to_bad_parameter(localizer)(_assert_url),
            )

            if click.confirm(localizer._("Do you want to load a Gramps family tree?")):
                configuration.extensions.append(
                    PluginInstanceConfiguration(
                        Gramps,
                        configuration=GrampsConfiguration(
                            family_trees=[
                                FamilyTreeConfiguration(
                                    await click.prompt(
                                        localizer._(
                                            "What is the path to your exported Gramps family tree file?"
                                        ),
                                        value_proc=user_facing_error_to_bad_parameter(
                                            localizer
                                        )(assert_path()),
                                    )
                                )
                            ]
                        ),
                    )
                )

            await write_configuration_file(
                configuration, configuration.configuration_file_path
            )
            click.secho(
                localizer._("Saved your project to {configuration_file}.").format(
                    configuration_file=str(configuration_file_path)
                ),
                fg="green",
            )

        return new


def _assert_project_configuration_file_path(value: Any) -> Path:
    configuration_file_path = assert_path()(value)
    if not configuration_file_path.suffix:
        configuration_file_path /= "betty.yaml"
    return configuration_file_path


def _assert_url(value: Any) -> str:
    url = assert_str()(value)
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme or "http"
    return f"{scheme}://{parsed_url.netloc}{parsed_url.path}"


async def _prompt_static_translations(
    locales: Sequence[str],
    text: str,
    default: Any | None = None,
    hide_input: bool = False,
    confirmation_prompt: bool | str = False,
    type: click.ParamType | Any | None = None,  # noqa A002
    value_proc: Callable[[str], Any] | None = None,
    prompt_suffix: str = ": ",
    show_default: bool = True,
    err: bool = False,
    show_choices: bool = True,
) -> StaticTranslations:
    return {
        locale: await click.prompt(
            text.format(locale=get_display_name(locale)),
            default,
            hide_input,
            confirmation_prompt,
            type,
            value_proc,
            prompt_suffix,
            show_default,
            err,
            show_choices,
        )
        for locale in locales
    }
