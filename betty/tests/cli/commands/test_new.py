from asyncio import to_thread
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from betty.config import assert_configuration_file
from betty.extension.gramps import Gramps
from betty.extension.gramps.config import GrampsConfiguration
from betty.project import ProjectConfiguration
from betty.tests.cli.test___init__ import run


class TestNew:
    async def _assert_new(
        self, project_directory_path: Path, inputs: Sequence[str]
    ) -> ProjectConfiguration:
        configuration_file_path = project_directory_path / "betty.yaml"
        await to_thread(run, "new", input="\n".join(inputs))
        configuration = ProjectConfiguration(configuration_file_path)
        return assert_configuration_file(configuration)(configuration_file_path)

    async def test_minimal(self, tmp_path: Path) -> None:
        title = "My First Project"
        author = "My First Author"
        base_url = "https://exampleexampleexample.com"
        root_path = "example"
        inputs = [
            str(tmp_path),
            title,
            "",
            author,
            f"{base_url}/{root_path}",
        ]
        configuration = await self._assert_new(tmp_path, inputs)
        assert configuration.title == title
        assert configuration.author == author

    async def test_with_base_url(self, tmp_path: Path) -> None:
        base_url = "https://exampleexampleexample.com"
        root_path = "example"
        inputs = [
            str(tmp_path),
            "My First Project",
            "",
            "My First Author",
            f"{base_url}/{root_path}",
        ]
        configuration = await self._assert_new(tmp_path, inputs)
        assert configuration.base_url == base_url
        assert configuration.root_path == root_path

    async def test_with_name(self, tmp_path: Path) -> None:
        name = "project-first-my"
        inputs = [
            str(tmp_path),
            "My First Project",
            name,
            "My First Author",
            "",
        ]
        configuration = await self._assert_new(tmp_path, inputs)
        assert configuration.name == name

    async def test_with_gramps(self, tmp_path: Path) -> None:
        gramps_family_tree_file_path = tmp_path / "gramps"
        inputs = [
            str(tmp_path),
            "My First Project",
            "",
            "My First Author",
            "",
            "y",
            str(gramps_family_tree_file_path),
        ]
        configuration = await self._assert_new(tmp_path, inputs)
        assert Gramps in configuration.extensions
        family_trees = cast(
            GrampsConfiguration,
            configuration.extensions[Gramps].extension_configuration,
        ).family_trees
        assert family_trees[0].file_path == gramps_family_tree_file_path

    async def test_with_single_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        inputs = [
            str(tmp_path),
            "My First Project",
            "",
            "My First Author",
            "",
            "n",
            "y",
            locale,
        ]
        configuration = await self._assert_new(tmp_path, inputs)
        locales = configuration.locales
        assert len(locales) == 1
        assert locale in locales

    async def test_with_multiple_locales(self, tmp_path: Path) -> None:
        default_locale = "nl-NL"
        other_locale = "uk"
        inputs = [
            str(tmp_path),
            "My First Project",
            "",
            "My First Author",
            "",
            "n",
            "y",
            default_locale,
            "y",
            other_locale,
        ]
        configuration = await self._assert_new(tmp_path, inputs)
        locales = configuration.locales
        assert len(locales) == 2
        assert locales.default.locale == default_locale
        assert other_locale in locales
