from pathlib import Path

from babel import Locale

from betty.commands.new import New
from betty.data import Data
from betty.file import read
from betty.loaders.gramps import Gramps, GrampsConfig
from betty.locale import default_locale_tag, to_language_tag
from betty.localizer import default_localizer
from betty.plugin.factory import NoPluginData
from betty.project import ProjectConfig
from betty.serializers.json import Json
from betty.test_utils.conftest import NewIsolatedApp
from betty.test_utils.console import run
from betty.test_utils.user.ui import StaticUi


async def _assert_new(configuration_file: Path) -> ProjectConfig:
    return ProjectConfig.definition.porter.load(
        Json().load(await read(configuration_file))
    )


class TestNew:
    async def test_configure__minimal(
        self, new_isolated_app: NewIsolatedApp, tmp_path: Path
    ) -> None:
        configuration_file = tmp_path / "betty.json"
        title = "My First Project"
        machine_name = "my-first-project"
        author = "My First Author"
        url = "https://exampleexampleexample.com/example"
        ui = StaticUi(
            confirmations=[
                None,
                None,
            ],
            inputs=[
                str(configuration_file),
                default_locale_tag,
                title,
                machine_name,
                author,
                url,
            ],
        )
        async with new_isolated_app(ui=ui) as app, app:
            await run(New(app), "new")
            configuration = await _assert_new(configuration_file)
        assert default_localizer.localize(configuration.title) == title
        assert configuration.name == "my-first-project"
        assert configuration.author is not None
        assert default_localizer.localize(configuration.author) == author
        assert configuration.url == url

    async def test_configure__with_project_directory(
        self, new_isolated_app: NewIsolatedApp, tmp_path: Path
    ) -> None:
        title = "My First Project"
        machine_name = "my-first-project"
        author = "My First Author"
        url = "https://exampleexampleexample.com/example"
        ui = StaticUi(
            confirmations=[
                None,
                None,
            ],
            inputs=[
                str(tmp_path),
                default_locale_tag,
                title,
                machine_name,
                author,
                url,
            ],
        )
        configuration_file = tmp_path / "betty.json"
        async with new_isolated_app(ui=ui) as app, app:
            await run(New(app), "new")
            await _assert_new(configuration_file)

    async def test_configure__with_single_locale(
        self,
        new_isolated_app: NewIsolatedApp,
        tmp_path: Path,
    ) -> None:
        configuration_file = tmp_path / "betty.json"
        locale = "nl-NL"
        ui = StaticUi(
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
        async with new_isolated_app(ui=ui) as app, app:
            await run(New(app), "new")
            configuration = await _assert_new(configuration_file)
        assert configuration.name == "mijn-eerste-project"
        locale_configurations = configuration.locales
        assert len(locale_configurations) == 1
        locale_configurations[locale]

    async def test_configure__with_multiple_locales(
        self,
        new_isolated_app: NewIsolatedApp,
        tmp_path: Path,
    ) -> None:
        configuration_file = tmp_path / "betty.json"
        default_locale = Locale("nl", "NL")
        other_locale = Locale("en", "US")
        ui = StaticUi(
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
        async with new_isolated_app(ui=ui) as app, app:
            await run(New(app), "new")
            configuration = await _assert_new(configuration_file)
        assert configuration.name == "mijn-eerste-project"
        assert len(configuration.locales) == 2

    async def test_configure__with_name(
        self,
        new_isolated_app: NewIsolatedApp,
        tmp_path: Path,
    ) -> None:
        configuration_file = tmp_path / "betty.json"
        name = "project-first-my"
        ui = StaticUi(
            confirmations=[
                None,
                None,
            ],
            inputs=[
                str(configuration_file),
                default_locale_tag,
                "My First Project",
                name,
                "My First Author",
                "https://exampleexampleexample.com/example",
            ],
        )
        async with new_isolated_app(ui=ui) as app, app:
            await run(New(app), "new")
            configuration = await _assert_new(configuration_file)
        assert configuration.name == name

    async def test_configure__with_gramps(
        self, new_isolated_app: NewIsolatedApp, tmp_path: Path
    ) -> None:
        configuration_file = tmp_path / "betty.json"
        gramps_family_tree_file = tmp_path / "gramps"
        ui = StaticUi(
            confirmations=[
                None,
                True,
            ],
            inputs=[
                str(configuration_file),
                default_locale_tag,
                "My First Project",
                "my-first-project",
                "My First Author",
                "https://exampleexampleexample.com/example",
                str(gramps_family_tree_file),
            ],
        )
        async with new_isolated_app(ui=ui) as app, app:
            await run(New(app), "new")
            configuration = await _assert_new(configuration_file)
            assert Gramps in configuration.loaders
            portable_gramps_configuration = configuration.loaders[Gramps].plugin_data
            assert portable_gramps_configuration is not NoPluginData
            assert not isinstance(portable_gramps_configuration, Data)
            gramps_configuration = GrampsConfig.definition.porter.load(
                portable_gramps_configuration
            )
            assert (
                gramps_configuration.family_trees[0].source == gramps_family_tree_file
            )
