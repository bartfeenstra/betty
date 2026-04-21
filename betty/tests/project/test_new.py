from pathlib import Path

from betty.app import App
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.serializer.json import Json
from betty.portable.file import assert_load_file
from betty.project.data import ProjectConfiguration
from betty.project.new import new, new_default_configuration


async def test_new(isolated_app: App, tmp_path: Path) -> None:
    project_directory = tmp_path / "my-first-project"
    configuration_file = project_directory / "betty.json"
    title = "My First Project"
    url = "https://exampleexampleexample.com/example"
    await new(
        isolated_app, ProjectConfiguration(title=title, url=url), configuration_file
    )
    configuration = ProjectConfiguration.data().porter.load(
        assert_load_file(serializers=[Json()])(configuration_file)
    )
    assert configuration.title.localize(DEFAULT_LOCALIZER) == title
    assert configuration.url == url


async def test_new_default_configuration() -> None:
    new_default_configuration(localizers=[DEFAULT_LOCALIZER])
