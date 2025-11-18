from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from typing_extensions import override

from betty.locale.localizable import Plain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import (
    ClassedPluginDefinition,
    DependentPluginDefinition,
    PluginTypeDefinition,
)
from betty.plugin.requirement import new_dependencies_requirement
from betty.requirement import HasRequirement, Requirement, StaticRequirement
from betty.test_utils.plugin import ClassedDummyPlugin, ClassedDummyPluginOne

if TYPE_CHECKING:
    from betty.app import App


class HasRequirementPlugin(HasRequirement):
    plugin: ClassVar[HasRequirementPluginDefinition]


class HasRequirementPluginDefinition(
    ClassedPluginDefinition[HasRequirementPlugin], DependentPluginDefinition
):
    plugin_type_cls = ClassedDummyPlugin
    type = PluginTypeDefinition(
        id="-",
        label=Plain("HasRequirement"),
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
    async def requirement(cls, *, app: App) -> Requirement:
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
    async def requirement(cls, *, app: App) -> Requirement:
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
