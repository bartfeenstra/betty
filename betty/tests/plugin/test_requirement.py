from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import override

from betty.locale.localizable import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import (
    ClassedPluginDefinition,
    DependentPluginDefinition,
    GlobalPluginRepositoryDefinition,
    PluginDefinition,
    PluginTypeDefinition,
)
from betty.plugin.requirement import get_requirement, new_dependencies_requirement
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.requirement import HasRequirement, Requirement, StaticRequirement
from betty.test_utils.plugin import (
    ClassedDummyPlugin,
    ClassedDummyPluginDefinition,
    ClassedDummyPluginOne,
)

if TYPE_CHECKING:
    from betty.app import App
    from betty.service_level import ServiceLevel


class HasRequirementPlugin(HasRequirement):
    plugin: ClassVar[HasRequirementPluginDefinition]


class HasRequirementPluginDefinition(
    ClassedPluginDefinition[HasRequirementPlugin], DependentPluginDefinition
):
    plugin_type_cls = ClassedDummyPlugin
    type = PluginTypeDefinition(
        id="-",
        label=Plain("HasRequirement"),
        repository=GlobalPluginRepositoryDefinition(
            lambda: StaticPluginRepository(HasRequirementPluginDefinition)
        ),
    )


@HasRequirementPluginDefinition(
    id="upstream-without-requirements",
    depends_on={"downstream-without-requirements"},
)
class UpstreamWithoutRequirements(HasRequirementPlugin):
    pass


@HasRequirementPluginDefinition(
    id="downstream-without-requirements",
)
class DownstreamWithoutRequirements(HasRequirementPlugin):
    pass


@HasRequirementPluginDefinition(
    id="upstream-with-unmet-requirements",
    depends_on={"downstream-with-unmet-requirements"},
)
class UpstreamWithUnmetRequirements(HasRequirementPlugin):
    pass


@HasRequirementPluginDefinition(
    id="downstream-with-unmet-requirements",
)
class DownstreamWithUnmetRequirements(HasRequirementPlugin):
    @override
    @classmethod
    async def requirement(cls, service_level: ServiceLevel, /) -> Requirement | None:
        return StaticRequirement(
            False,
            Plain("downstream-requirement-summary"),
            Plain("downstream-requirement-details"),
        )


@HasRequirementPluginDefinition(
    id="upstream-with-met-requirements",
    depends_on={"downstream-with-met-requirements"},
)
class UpstreamWithMetRequirements(HasRequirementPlugin):
    pass


@HasRequirementPluginDefinition(
    id="downstream-with-met-requirements",
)
class DownstreamWithMetRequirements(HasRequirementPlugin):
    @override
    @classmethod
    async def requirement(cls, service_level: ServiceLevel, /) -> Requirement | None:
        return StaticRequirement(
            True,
            Plain("downstream-requirement-summary"),
            Plain("downstream-requirement-details"),
        )


async def test_new_dependencies_requirement__without_dependent_plugin(
    temporary_app: App,
) -> None:
    actual = await new_dependencies_requirement(
        ClassedDummyPluginOne.plugin,
        [ClassedDummyPluginOne.plugin],
        app=temporary_app,
    )
    assert actual is None


async def test_new_dependencies_requirement__without_requirements(
    temporary_app: App,
) -> None:
    plugins = [UpstreamWithoutRequirements.plugin, DownstreamWithoutRequirements.plugin]
    actual = await new_dependencies_requirement(
        UpstreamWithoutRequirements.plugin, plugins, app=temporary_app
    )
    assert actual is None


async def test_new_dependencies_requirement__with_unmet_requirements(
    temporary_app: App,
) -> None:
    plugins = [
        UpstreamWithUnmetRequirements.plugin,
        DownstreamWithUnmetRequirements.plugin,
    ]
    actual = await new_dependencies_requirement(
        UpstreamWithUnmetRequirements.plugin, plugins, app=temporary_app
    )
    assert actual is not None
    assert not actual.is_met()
    message = actual.localize(DEFAULT_LOCALIZER)
    assert UpstreamWithUnmetRequirements.plugin.id in message
    assert DownstreamWithUnmetRequirements.plugin.id in message


async def test_new_dependencies_requirement__with_met_requirements(
    temporary_app: App,
) -> None:
    plugins = [UpstreamWithMetRequirements.plugin, DownstreamWithMetRequirements.plugin]
    actual = await new_dependencies_requirement(
        UpstreamWithMetRequirements.plugin, plugins, app=temporary_app
    )
    assert actual is not None
    assert actual.is_met()
    message = actual.localize(DEFAULT_LOCALIZER)
    assert UpstreamWithMetRequirements.plugin.id in message
    assert DownstreamWithMetRequirements.plugin.id in message


async def test_get_requirement__minimal_with_app(temporary_app: App) -> None:
    assert await get_requirement(PluginDefinition(id="-"), temporary_app) is None


async def test_get_requirement__minimal_with_project(temporary_app: App) -> None:
    async with Project.new_temporary(temporary_app) as project, project:
        assert await get_requirement(PluginDefinition(id="-"), project) is None


async def test_get_requirement__minimal_classed_with_app(temporary_app: App) -> None:
    @ClassedDummyPluginDefinition(
        id="-",
    )
    class _Plugin(ClassedDummyPlugin):
        pass

    assert await get_requirement(_Plugin.plugin, temporary_app) is None


async def test_get_requirement__minimal_classed_with_project(
    temporary_app: App,
) -> None:
    @ClassedDummyPluginDefinition(
        id="-",
    )
    class _Plugin(ClassedDummyPlugin):
        pass

    async with Project.new_temporary(temporary_app) as project, project:
        assert await get_requirement(_Plugin.plugin, project) is None


async def test_get_requirement__with_has_requirement_with_app(
    temporary_app: App,
) -> None:
    requirement = StaticRequirement(True, Plain(""))

    @HasRequirementPluginDefinition(
        id="-",
    )
    class _Plugin(HasRequirementPlugin):
        @override
        @classmethod
        async def requirement(
            cls, service_level: ServiceLevel, /
        ) -> Requirement | None:
            return requirement

    assert await get_requirement(_Plugin.plugin, temporary_app) is requirement


async def test_get_requirement__with_has_requirement_with_project(
    temporary_app: App,
) -> None:
    requirement = StaticRequirement(True, Plain(""))

    @HasRequirementPluginDefinition(
        id="-",
    )
    class _Plugin(HasRequirementPlugin):
        @override
        @classmethod
        async def requirement(
            cls, service_level: ServiceLevel, /
        ) -> Requirement | None:
            return requirement

    async with Project.new_temporary(temporary_app) as project, project:
        assert await get_requirement(_Plugin.plugin, project) is requirement
