from betty.app import App
from betty.model import EntityDefinition
from betty.plugins.extension.raspberry_mint.region import Region
from betty.project import Project
from betty.test_utils.model import DummyEntityOne


class TestRegion:
    async def test_all(self, isolated_app: App) -> None:
        async with (
            Project.new_isolated(
                isolated_app,
                plugins={
                    EntityDefinition: [DummyEntityOne],
                },
            ) as project,
            project,
        ):
            assert "entity-page-content--dummy-one" in await Region.all(project)

    def test_resolve__with_enum(self) -> None:
        assert Region.resolve(Region.FRONT_PAGE_CONTENT) == "front-page-content"

    def test_resolve__with_string(self) -> None:
        assert Region.resolve("my-first-region") == "my-first-region"
