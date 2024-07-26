from __future__ import annotations  # noqa D100

from typing import Any, TYPE_CHECKING
from urllib.parse import urlparse

import click

from betty.assertion import assert_path, assert_str, assert_locale
from betty.cli import assertion_to_value_proc
from betty.cli.commands import command, pass_app
from betty.config import write_configuration_file
from betty.extension.cotton_candy import CottonCandy
from betty.extension.deriver import Deriver
from betty.extension.gramps import Gramps
from betty.extension.gramps.config import GrampsConfiguration, FamilyTreeConfiguration
from betty.extension.http_api_doc import HttpApiDoc
from betty.extension.maps import Maps
from betty.extension.trees import Trees
from betty.extension.webpack import Webpack
from betty.extension.wikipedia import Wikipedia
from betty.extension.privatizer import Privatizer
from betty.locale import DEFAULT_LOCALE
from betty.machine_name import assert_machine_name, machinify
from betty.project import (
    ProjectConfiguration,
    ExtensionConfiguration,
    LocaleConfiguration,
)
from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App
    from pathlib import Path


def _assert_project_configuration_file_path(value: Any) -> Path:
    configuration_file_path = assert_path()(value)
    if not configuration_file_path.suffix:
        configuration_file_path /= "betty.yaml"
    return configuration_file_path


def _assert_url(value: Any) -> tuple[str, str]:
    url = assert_str()(value)
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme or "http"
    return f"{scheme}://{parsed_url.netloc}", parsed_url.path


@internal
@click.command(help="Create a new project.")
@pass_app
@command
async def new(app: App) -> None:  # noqa D103
    configuration_file_path = click.prompt(
        app.localizer._("Where do you want to save your project's configuration file?"),
        value_proc=assertion_to_value_proc(
            _assert_project_configuration_file_path, app.localizer
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

    configuration.title = click.prompt(app.localizer._("What is your project called?"))

    configuration.name = click.prompt(
        app.localizer._("What is your project's machine name? "),
        default=machinify(configuration.title),
        value_proc=assertion_to_value_proc(assert_machine_name, app.localizer),
    )

    configuration.author = click.prompt(app.localizer._("Who is the author?"))

    configuration.base_url, configuration.root_path = click.prompt(
        app.localizer._("At which URL will your site be published?"),
        default="https://example.com",
        value_proc=assertion_to_value_proc(_assert_url, app.localizer),
    )

    if click.confirm(app.localizer._("Do you want to load a Gramps family tree?")):
        configuration.extensions.append(
            ExtensionConfiguration(
                Gramps,
                extension_configuration=GrampsConfiguration(
                    family_trees=[
                        FamilyTreeConfiguration(
                            click.prompt(
                                app.localizer._(
                                    "What is the path to your exported Gramps family tree file?"
                                ),
                                value_proc=assertion_to_value_proc(
                                    assert_path(), app.localizer
                                ),
                            )
                        )
                    ]
                ),
            )
        )

    configuration.locales.replace(
        LocaleConfiguration(
            click.prompt(
                app.localizer._(
                    "Which language should your project site be generated in? Enter an IETF BCP 47 language code."
                ),
                default=DEFAULT_LOCALE,
                value_proc=assertion_to_value_proc(assert_locale(), app.localizer),
            )
        )
    )
    while click.confirm(app.localizer._("Do you want to add another locale?")):
        configuration.locales.append(
            LocaleConfiguration(
                click.prompt(
                    app.localizer._(
                        "Which language should your project site be generated in?"
                    ),
                    value_proc=assertion_to_value_proc(assert_locale(), app.localizer),
                )
            )
        )

    await write_configuration_file(configuration, configuration.configuration_file_path)
    click.secho(
        app.localizer._("Saved your project to {configuration_file}.").format(
            configuration_file=str(configuration_file_path)
        ),
        fg="green",
    )
