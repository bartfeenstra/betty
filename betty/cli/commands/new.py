from __future__ import annotations  # noqa D100

from typing import Any, TYPE_CHECKING
from urllib.parse import urlparse

import click
from betty.assertion import assert_path, assert_str, assert_locale
from betty.cli.commands import command, pass_app
from betty.cli.error import user_facing_error_to_bad_parameter
from betty.config import write_configuration_file
from betty.project.extension.cotton_candy import CottonCandy
from betty.project.extension.deriver import Deriver
from betty.project.extension.gramps import Gramps
from betty.project.extension.gramps.config import (
    GrampsConfiguration,
    FamilyTreeConfiguration,
)
from betty.project.extension.http_api_doc import HttpApiDoc
from betty.project.extension.maps import Maps
from betty.project.extension.privatizer import Privatizer
from betty.project.extension.trees import Trees
from betty.project.extension.webpack import Webpack
from betty.project.extension.wikipedia import Wikipedia
from betty.locale import DEFAULT_LOCALE, get_display_name
from betty.machine_name import assert_machine_name, machinify
from betty.project.config import (
    ProjectConfiguration,
    ExtensionConfiguration,
    LocaleConfiguration,
)
from betty.typing import internal

if TYPE_CHECKING:
    from betty.locale.localizable import StaticTranslations
    from collections.abc import Callable, Sequence
    from betty.app import App
    from pathlib import Path


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


@internal
@command(help="Create a new project.")
@pass_app
async def new(app: App) -> None:  # noqa D103
    localizer = await app.localizer
    configuration_file_path = click.prompt(
        localizer._("Where do you want to save your project's configuration file?"),
        value_proc=user_facing_error_to_bad_parameter(localizer)(
            _assert_project_configuration_file_path
        ),
    )
    configuration = ProjectConfiguration(
        configuration_file_path,
    )

    configuration.extensions.enable(CottonCandy)
    configuration.extensions.enable(Deriver)
    configuration.extensions.enable(Privatizer)
    configuration.extensions.enable(Wikipedia)
    if await Webpack.enable_requirement().is_met():
        configuration.extensions.enable(HttpApiDoc)
        configuration.extensions.enable(Maps)
        configuration.extensions.enable(Trees)

    configuration.locales.replace(
        LocaleConfiguration(
            click.prompt(
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
                click.prompt(
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

    configuration.title = _prompt_static_translations(
        locales,
        localizer._("What is your project called in {locale}?"),
    )

    configuration.name = click.prompt(
        localizer._("What is your project's machine name?"),
        default=machinify(
            configuration.title.localize(
                await app.localizers.get(configuration.locales.default.locale)
            )
        ),
        value_proc=user_facing_error_to_bad_parameter(localizer)(assert_machine_name()),
    )

    configuration.author = _prompt_static_translations(
        locales,
        localizer._("What is the project author called in {locale}?"),
    )

    configuration.url = click.prompt(
        localizer._("At which URL will your site be published?"),
        default="https://example.com",
        value_proc=user_facing_error_to_bad_parameter(localizer)(_assert_url),
    )

    if click.confirm(localizer._("Do you want to load a Gramps family tree?")):
        configuration.extensions.append(
            ExtensionConfiguration(
                Gramps,
                extension_configuration=GrampsConfiguration(
                    family_trees=[
                        FamilyTreeConfiguration(
                            click.prompt(
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

    await write_configuration_file(configuration, configuration.configuration_file_path)
    click.secho(
        localizer._("Saved your project to {configuration_file}.").format(
            configuration_file=str(configuration_file_path)
        ),
        fg="green",
    )


def _prompt_static_translations(
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
        locale: click.prompt(
            text.format(locale=get_display_name(locale)),
            default,
            hide_input,
            confirmation_prompt,  # type: ignore[arg-type]
            type,
            value_proc,  # type: ignore[arg-type]
            prompt_suffix,
            show_default,
            err,
            show_choices,
        )
        for locale in locales
    }
