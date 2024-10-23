from collections.abc import Sequence
from pathlib import Path

from betty.app import App
from betty.config import assert_configuration_file
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project
from betty.project.config import ProjectConfiguration
from betty.project.extension.gramps import Gramps
from betty.test_utils.cli import run


class TestNew:
    async def _assert_new(
        self, app: App, project_directory_path: Path, inputs: Sequence[str]
    ) -> ProjectConfiguration:
        configuration_file_path = project_directory_path / "betty.yaml"
        await run(app, "new", input="\n".join(inputs))
        configuration = await ProjectConfiguration.new(configuration_file_path)
        return (await assert_configuration_file(configuration))(configuration_file_path)

    async def test_click_command_minimal(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        title = "My First Project"
        author = "My First Author"
        url = "https://exampleexampleexample.com/example"
        inputs = [
            str(tmp_path),
            "",
            "",
            title,
            "",
            author,
            url,
        ]
        configuration = await self._assert_new(new_temporary_app, tmp_path, inputs)
        assert configuration.title.localize(DEFAULT_LOCALIZER) == title
        assert configuration.name == "my-first-project"
        assert configuration.author.localize(DEFAULT_LOCALIZER) == author
        assert configuration.url == url

    async def test_click_command_with_single_locale(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        locale = "nl-NL"
        inputs = [
            str(tmp_path),
            locale,
            "",
            "Mijn Eerste Project",
            "",
            "Mijn Eerste Auteur",
            "",
        ]
        configuration = await self._assert_new(new_temporary_app, tmp_path, inputs)
        assert configuration.name == "mijn-eerste-project"
        locale_configurations = configuration.locales
        assert len(locale_configurations) == 1
        locale_configurations[locale]

    async def test_click_command_with_multiple_locales(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        default_locale = "nl-NL"
        other_locale = "en-US"
        inputs = [
            str(tmp_path),
            default_locale,
            "y",
            other_locale,
            "",
            "Mijn Eerste Project",
            "My First Project",
            "",
            "Mijn Eerste Auteur",
            "My First Author",
            "",
            "",
        ]
        configuration = await self._assert_new(new_temporary_app, tmp_path, inputs)
        assert configuration.name == "mijn-eerste-project"
        locale_configurations = configuration.locales
        assert len(locale_configurations) == 2
        assert locale_configurations.default.locale == default_locale
        locale_configurations[other_locale]

    async def test_click_command_with_name(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        name = "project-first-my"
        inputs = [
            str(tmp_path),
            "",
            "",
            "My First Project",
            name,
            "My First Author",
            "",
            "",
        ]
        configuration = await self._assert_new(new_temporary_app, tmp_path, inputs)
        assert configuration.name == name

    async def test_click_command_with_gramps(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        gramps_family_tree_file_path = tmp_path / "gramps"
        inputs = [
            str(tmp_path),
            "",
            "",
            "My First Project",
            "",
            "My First Author",
            "",
            "y",
            str(gramps_family_tree_file_path),
        ]
        configuration = await self._assert_new(new_temporary_app, tmp_path, inputs)
        assert Gramps in configuration.extensions
        async with Project.new_temporary(new_temporary_app) as project, project:
            gramps = await configuration.extensions[Gramps].new_plugin_instance(
                project.extension_repository
            )
        assert isinstance(gramps, Gramps)
        assert (
            gramps.configuration.family_trees[0].file_path
            == gramps_family_tree_file_path
        )
