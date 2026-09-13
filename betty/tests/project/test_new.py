from pathlib import Path

from betty.app import App
from betty.localizer import default_localizer
from betty.portable.file import assert_load_file
from betty.project import ProjectConfig
from betty.project.new import new
from betty.serializers.json import Json


async def test_new(isolated_app: App, tmp_path: Path) -> None:
    project_directory = tmp_path / "my-first-project"
    configuration_file = project_directory / "betty.json"
    title = "My First Project"
    url = "https://exampleexampleexample.com/example"
    await new(isolated_app, ProjectConfig(title=title, url=url), configuration_file)
    configuration = ProjectConfig.data().porter.load(
        assert_load_file(serializers=[Json()])(configuration_file)
    )
    assert configuration.title.localize(default_localizer) == title
    assert configuration.url == url
