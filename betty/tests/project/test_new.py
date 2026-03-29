from pathlib import Path

from babel import Locale

from betty.data import Data
from betty.locale import DEFAULT_LOCALE_TAG, to_language_tag
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.loader.gramps import Gramps, GrampsConfiguration
from betty.portable.file import assert_load_file
from betty.project.data import ProjectConfiguration
from betty.project.new import new
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.user import StaticUser
from betty.typing import Void


async def _assert_new(configuration_file_path: Path) -> ProjectConfiguration:
    return ProjectConfiguration.data().porter.load(
        (await assert_load_file())(configuration_file_path)
    )


async def test_new__minimal(
    isolated_app_factory: IsolatedAppFactory, tmp_path: Path
) -> None:
    configuration_file_path = tmp_path / "betty.json"
    title = "My First Project"
    machine_name = "my-first-project"
    author = "My First Author"
    url = "https://exampleexampleexample.com/example"
    user = StaticUser(
        confirmations=[
            None,
            None,
        ],
        inputs=[
            str(configuration_file_path),
            DEFAULT_LOCALE_TAG,
            title,
            machine_name,
            author,
            url,
        ],
    )
    async with isolated_app_factory(user=user) as app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
    assert configuration.title.localize(DEFAULT_LOCALIZER) == title
    assert configuration.name == "my-first-project"
    assert configuration.author is not None
    assert configuration.author.localize(DEFAULT_LOCALIZER) == author
    assert configuration.url == url


async def test_new__with_project_directory(
    isolated_app_factory: IsolatedAppFactory, tmp_path: Path
) -> None:
    title = "My First Project"
    machine_name = "my-first-project"
    author = "My First Author"
    url = "https://exampleexampleexample.com/example"
    user = StaticUser(
        confirmations=[
            None,
            None,
        ],
        inputs=[
            str(tmp_path),
            DEFAULT_LOCALE_TAG,
            title,
            machine_name,
            author,
            url,
        ],
    )
    configuration_file_path = tmp_path / "betty.yaml"
    async with isolated_app_factory(user=user) as app:
        await new(app)
        await _assert_new(configuration_file_path)


async def test_new__with_single_locale(
    isolated_app_factory: IsolatedAppFactory,
    tmp_path: Path,
) -> None:
    configuration_file_path = tmp_path / "betty.yaml"
    locale = "nl-NL"
    user = StaticUser(
        confirmations=[
            None,
            None,
        ],
        inputs=[
            str(configuration_file_path),
            locale,
            "Mijn Eerste Project",
            "mijn-eerste-project",
            "Mijn Eerste Auteur",
            "https://exampleexampleexample.com/example",
        ],
    )
    async with isolated_app_factory(user=user) as app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
    assert configuration.name == "mijn-eerste-project"
    locale_configurations = configuration.locales
    assert len(locale_configurations) == 1
    locale_configurations[locale]


async def test_new__with_multiple_locales(
    isolated_app_factory: IsolatedAppFactory,
    tmp_path: Path,
) -> None:
    configuration_file_path = tmp_path / "betty.yaml"
    default_locale = Locale("nl", "NL")
    other_locale = Locale("en", "US")
    user = StaticUser(
        confirmations=[
            True,
            None,
            None,
        ],
        inputs=[
            str(configuration_file_path),
            to_language_tag(default_locale),
            to_language_tag(other_locale),
            "Mijn Eerste Project",
            "My First Project",
            "mijn-eerste-project",
            "Mijn Eerste Auteur",
            "My First Author",
            "https://exampleexampleexample.com/example",
        ],
    )
    async with isolated_app_factory(user=user) as app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
    assert configuration.name == "mijn-eerste-project"
    assert len(configuration.locales) == 2


async def test_new__with_name(
    isolated_app_factory: IsolatedAppFactory,
    tmp_path: Path,
) -> None:
    configuration_file_path = tmp_path / "betty.yaml"
    name = "project-first-my"
    user = StaticUser(
        confirmations=[
            None,
            None,
        ],
        inputs=[
            str(configuration_file_path),
            DEFAULT_LOCALE_TAG,
            "My First Project",
            name,
            "My First Author",
            "https://exampleexampleexample.com/example",
        ],
    )
    async with isolated_app_factory(user=user) as app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
    assert configuration.name == name


async def test_new__with_gramps(
    isolated_app_factory: IsolatedAppFactory, tmp_path: Path
) -> None:
    configuration_file_path = tmp_path / "betty.yaml"
    gramps_family_tree_file_path = tmp_path / "gramps"
    user = StaticUser(
        confirmations=[
            None,
            True,
        ],
        inputs=[
            str(configuration_file_path),
            DEFAULT_LOCALE_TAG,
            "My First Project",
            "my-first-project",
            "My First Author",
            "https://exampleexampleexample.com/example",
            str(gramps_family_tree_file_path),
        ],
    )
    async with isolated_app_factory(user=user) as app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
        assert Gramps in configuration.loaders
        portable_gramps_configuration = configuration.loaders[Gramps].plugin_data
        assert portable_gramps_configuration is not Void
        assert not isinstance(portable_gramps_configuration, Data)
        gramps_configuration = GrampsConfiguration.data().porter.load(
            portable_gramps_configuration
        )
        assert (
            gramps_configuration.family_trees[0].source == gramps_family_tree_file_path
        )
