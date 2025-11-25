from pathlib import Path

from pytest_mock import MockerFixture

from betty.config.file import assert_configuration_file
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project
from betty.project.config import ProjectConfiguration
from betty.project.extension import ExtensionPlugin
from betty.project.extension.gramps import Gramps
from betty.project.new import new
from betty.test_utils.conftest import TemporaryAppFactory
from betty.test_utils.user import StaticUser


async def _assert_new(configuration_file_path: Path) -> ProjectConfiguration:
    configuration = ProjectConfiguration(Path())
    return (await assert_configuration_file(configuration))(configuration_file_path)


async def test_new__minimal(
    mocker: MockerFixture,
    temporary_app_factory: TemporaryAppFactory,
    tmp_path: Path,
) -> None:
    mocker.patch(
        "betty.project.extension.webpack.Webpack.requirement"
    ).return_value = None
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
            DEFAULT_LOCALE,
            title,
            machine_name,
            author,
            url,
        ],
    )
    async with temporary_app_factory(user=user) as app, app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
    assert configuration.title.localize(DEFAULT_LOCALIZER) == title
    assert configuration.name == "my-first-project"
    assert configuration.author is not None
    assert configuration.author.localize(DEFAULT_LOCALIZER) == author
    assert configuration.url == url


async def test_new__with_project_directory(
    mocker: MockerFixture,
    temporary_app_factory: TemporaryAppFactory,
    tmp_path: Path,
) -> None:
    mocker.patch(
        "betty.project.extension.webpack.Webpack.requirement"
    ).return_value = None
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
            DEFAULT_LOCALE,
            title,
            machine_name,
            author,
            url,
        ],
    )
    configuration_file_path = tmp_path / "betty.yaml"
    async with temporary_app_factory(user=user) as app, app:
        await new(app)
        await _assert_new(configuration_file_path)


async def test_new__with_single_locale(
    temporary_app_factory: TemporaryAppFactory,
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
    async with temporary_app_factory(user=user) as app, app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
    assert configuration.name == "mijn-eerste-project"
    locale_configurations = configuration.locales
    assert len(locale_configurations) == 1
    locale_configurations[locale]


async def test_new__with_multiple_locales(
    temporary_app_factory: TemporaryAppFactory,
    tmp_path: Path,
) -> None:
    configuration_file_path = tmp_path / "betty.yaml"
    default_locale = "nl-NL"
    other_locale = "en-US"
    user = StaticUser(
        confirmations=[
            True,
            None,
            None,
        ],
        inputs=[
            str(configuration_file_path),
            default_locale,
            other_locale,
            "Mijn Eerste Project",
            "My First Project",
            "mijn-eerste-project",
            "Mijn Eerste Auteur",
            "My First Author",
            "https://exampleexampleexample.com/example",
        ],
    )
    async with temporary_app_factory(user=user) as app, app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
    assert configuration.name == "mijn-eerste-project"
    locale_configurations = configuration.locales
    assert len(locale_configurations) == 2
    assert locale_configurations.default.locale == default_locale
    locale_configurations[other_locale]


async def test_new__with_name(
    temporary_app_factory: TemporaryAppFactory,
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
            DEFAULT_LOCALE,
            "My First Project",
            name,
            "My First Author",
            "https://exampleexampleexample.com/example",
        ],
    )
    async with temporary_app_factory(user=user) as app, app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
    assert configuration.name == name


async def test_new__with_gramps(
    temporary_app_factory: TemporaryAppFactory,
    tmp_path: Path,
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
            DEFAULT_LOCALE,
            "My First Project",
            "my-first-project",
            "My First Author",
            "https://exampleexampleexample.com/example",
            str(gramps_family_tree_file_path),
        ],
    )
    async with temporary_app_factory(user=user) as app, app:
        await new(app)
        configuration = await _assert_new(configuration_file_path)
        assert Gramps.plugin in configuration.extensions
        async with Project.new_temporary(app) as project, project:
            gramps = await configuration.extensions[Gramps.plugin].new_plugin_instance(
                await project.plugins(ExtensionPlugin), factory=project.new_target
            )
            assert isinstance(gramps, Gramps)
            assert (
                gramps.configuration.family_trees[0].source
                == gramps_family_tree_file_path
            )
