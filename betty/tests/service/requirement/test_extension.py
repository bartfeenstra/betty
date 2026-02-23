import pytest

from betty.app import App
from betty.exception import HumanFacingException
from betty.extension import ExtensionDefinition
from betty.project import Project
from betty.service.level import ServiceLevel
from betty.service.requirement.extension import require_extension
from betty.test_utils.project.extension import DummyExtensionOne


@require_extension(DummyExtensionOne)
def _require_extension_target(extension: DummyExtensionOne, /) -> DummyExtensionOne:
    return extension


async def test_require_extension__with_universe() -> None:
    with pytest.raises(HumanFacingException):
        await _require_extension_target(
            ServiceLevel(plugins={ExtensionDefinition: [DummyExtensionOne]})
        )


async def test_require_extension__with_app() -> None:
    async with (
        App.new_isolated(plugins={ExtensionDefinition: [DummyExtensionOne]}) as app,
        app,
    ):
        with pytest.raises(HumanFacingException):
            await _require_extension_target(app)


async def test_require_extension__with_project_with_extension_plugin_not_found(
    isolated_app: App,
) -> None:
    async with Project.new_isolated(isolated_app) as project, project:
        with pytest.raises(HumanFacingException):
            await _require_extension_target(project)


async def test_require_extension__with_project_without_extension(
    isolated_app: App,
) -> None:
    async with (
        Project.new_isolated(
            isolated_app, plugins={ExtensionDefinition: [DummyExtensionOne]}
        ) as project,
        project,
    ):
        with pytest.raises(HumanFacingException):
            await _require_extension_target(project)


async def test_require_extension__with_extension(isolated_app: App) -> None:
    async with Project.new_isolated(
        isolated_app, plugins={ExtensionDefinition: [DummyExtensionOne]}
    ) as project:
        project.configuration.extensions.add(DummyExtensionOne)
        async with project:
            assert isinstance(
                await _require_extension_target(project), DummyExtensionOne
            )
