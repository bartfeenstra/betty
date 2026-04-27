from betty.entity import EntityDefinition
from betty.plugins.extension.raspberry_mint.region import Region
from betty.test_utils.conftest import IsolatedAppFactory, IsolatedProjectFactory
from betty.test_utils.entity import DummyEntityOne


class TestRegion:
    async def test_all(
        self,
        isolated_app_factory: IsolatedAppFactory,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_app_factory(
                plugins={
                    EntityDefinition: [DummyEntityOne],
                }
            ) as app,
            isolated_project_factory(
                app=app, generate_entity_list_html=[DummyEntityOne]
            ) as project,
        ):
            assert "entity-page-content--dummy-one" in await Region.all(project)

    def test_resolve__with_enum(self) -> None:
        assert Region.resolve(Region.FRONT_PAGE_CONTENT) == "front-page-content"

    def test_resolve__with_string(self) -> None:
        assert Region.resolve("my-first-region") == "my-first-region"
