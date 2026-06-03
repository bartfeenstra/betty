from pathlib import Path

from babel import Locale

from betty.data import Data
from betty.loaders.gramps import Gramps, GrampsData
from betty.locale import DEFAULT_LOCALE_TAG, to_language_tag
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.portable.file import assert_load_file
from betty.project import ProjectData
from betty.serializers.json import Json
from betty.test_utils.conftest import IsolatedAppFactory
from betty.test_utils.console import run
from betty.test_utils.user import StaticUser
from betty.typing import Void


def _assert_new(configuration_file: Path) -> ProjectData:
    return ProjectData.data().porter.load(
        assert_load_file(serializers=[Json()])(configuration_file)
    )


class TestNew:
    async def test_configure__minimal(
        self, isolated_app_factory: IsolatedAppFactory, tmp_path: Path
    ) -> None:
        configuration_file = tmp_path / "betty.json"
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
                str(configuration_file),
                DEFAULT_LOCALE_TAG,
                title,
                machine_name,
                author,
                url,
            ],
        )
        async with isolated_app_factory(user=user) as app:
            await run(app, "new")
            configuration = _assert_new(configuration_file)
        assert configuration.title.localize(DEFAULT_LOCALIZER) == title
        assert configuration.name == "my-first-project"
        assert configuration.author is not None
        assert configuration.author.localize(DEFAULT_LOCALIZER) == author
        assert configuration.url == url

    async def test_configure__with_project_directory(
        self, isolated_app_factory: IsolatedAppFactory, tmp_path: Path
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
        configuration_file = tmp_path / "betty.json"
        async with isolated_app_factory(user=user) as app:
            await run(app, "new")
            _assert_new(configuration_file)

    async def test_configure__with_single_locale(
        self,
        isolated_app_factory: IsolatedAppFactory,
        tmp_path: Path,
    ) -> None:
        configuration_file = tmp_path / "betty.json"
        locale = "nl-NL"
        user = StaticUser(
            confirmations=[
                None,
                None,
            ],
            inputs=[
                str(configuration_file),
                locale,
                "Mijn Eerste Project",
                "mijn-eerste-project",
                "Mijn Eerste Auteur",
                "https://exampleexampleexample.com/example",
            ],
        )
        async with isolated_app_factory(user=user) as app:
            await run(app, "new")
            configuration = _assert_new(configuration_file)
        assert configuration.name == "mijn-eerste-project"
        locale_configurations = configuration.locales
        assert len(locale_configurations) == 1
        locale_configurations[locale]

    async def test_configure__with_multiple_locales(
        self,
        isolated_app_factory: IsolatedAppFactory,
        tmp_path: Path,
    ) -> None:
        configuration_file = tmp_path / "betty.json"
        default_locale = Locale("nl", "NL")
        other_locale = Locale("en", "US")
        user = StaticUser(
            confirmations=[
                True,
                None,
                None,
            ],
            inputs=[
                str(configuration_file),
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
            await run(app, "new")
            configuration = _assert_new(configuration_file)
        assert configuration.name == "mijn-eerste-project"
        assert len(configuration.locales) == 2

    async def test_configure__with_name(
        self,
        isolated_app_factory: IsolatedAppFactory,
        tmp_path: Path,
    ) -> None:
        configuration_file = tmp_path / "betty.json"
        name = "project-first-my"
        user = StaticUser(
            confirmations=[
                None,
                None,
            ],
            inputs=[
                str(configuration_file),
                DEFAULT_LOCALE_TAG,
                "My First Project",
                name,
                "My First Author",
                "https://exampleexampleexample.com/example",
            ],
        )
        async with isolated_app_factory(user=user) as app:
            await run(app, "new")
            configuration = _assert_new(configuration_file)
        assert configuration.name == name

    async def test_configure__with_gramps(
        self, isolated_app_factory: IsolatedAppFactory, tmp_path: Path
    ) -> None:
        configuration_file = tmp_path / "betty.json"
        gramps_family_tree_file = tmp_path / "gramps"
        user = StaticUser(
            confirmations=[
                None,
                True,
            ],
            inputs=[
                str(configuration_file),
                DEFAULT_LOCALE_TAG,
                "My First Project",
                "my-first-project",
                "My First Author",
                "https://exampleexampleexample.com/example",
                str(gramps_family_tree_file),
            ],
        )
        async with isolated_app_factory(user=user) as app:
            await run(app, "new")
            configuration = _assert_new(configuration_file)
            assert Gramps in configuration.loaders
            portable_gramps_configuration = configuration.loaders[Gramps].plugin_data
            assert portable_gramps_configuration is not Void
            assert not isinstance(portable_gramps_configuration, Data)
            gramps_configuration = GrampsData.data().porter.load(
                portable_gramps_configuration
            )
            assert (
                gramps_configuration.family_trees[0].source == gramps_family_tree_file
            )
