from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pytest
from typing_extensions import override

from betty.locale.localizable import CountablePlain
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.error import PluginNotFound
from betty.plugin.requirement import (
    CheckRequirementRepository,
    CyclicDependencyError,
    get_requirement,
    new_dependencies_requirement,
)
from betty.requirement import HasRequirement, Requirement, StaticRequirement
from betty.test_utils.plugin import DummyPlugin, DummyPluginDefinition, DummyPluginOne

if TYPE_CHECKING:
    from betty.app import App
    from betty.service.level import ServiceLevel


class HasRequirementPlugin(HasRequirement, Plugin):
    plugin: ClassVar[HasRequirementPluginDefinition]


class HasRequirementPluginDefinition(DependentPluginDefinition):
    plugin_type_cls = DummyPlugin
    type = PluginTypeDefinition(
        "-",
        "HasRequirement",
        "HasRequirement",
        CountablePlain("{count} HasRequirement", "{count} HasRequirements"),
    )


@HasRequirementPluginDefinition(
    "upstream-without-requirements", depends_on={"downstream-without-requirements"}
)
class UpstreamWithoutRequirements(HasRequirementPlugin):
    pass


@HasRequirementPluginDefinition("downstream-without-requirements")
class DownstreamWithoutRequirements(HasRequirementPlugin):
    pass


@HasRequirementPluginDefinition(
    "upstream-with-unmet-requirements",
    depends_on={"downstream-with-unmet-requirements"},
)
class UpstreamWithUnmetRequirements(HasRequirementPlugin):
    @override
    @classmethod
    async def requirement(cls, level: ServiceLevel, /) -> Requirement | None:
        return StaticRequirement(
            "upstream-requirement-summary",
            "upstream-requirement-details",
        )


@HasRequirementPluginDefinition("downstream-with-unmet-requirements")
class DownstreamWithUnmetRequirements(HasRequirementPlugin):
    @override
    @classmethod
    async def requirement(cls, level: ServiceLevel, /) -> Requirement | None:
        return StaticRequirement(
            "downstream-requirement-summary",
            "downstream-requirement-details",
        )


@HasRequirementPluginDefinition(
    "upstream-with-met-requirements", depends_on={"downstream-with-met-requirements"}
)
class UpstreamWithMetRequirements(HasRequirementPlugin):
    pass


@HasRequirementPluginDefinition("downstream-with-met-requirements")
class DownstreamWithMetRequirements(HasRequirementPlugin):
    pass


async def test_new_dependencies_requirement__without_dependent_plugin(
    temporary_app: App,
) -> None:
    actual = await new_dependencies_requirement(
        DummyPluginOne.plugin,
        [DummyPluginOne.plugin],
        services=temporary_app,
    )
    assert actual is None


async def test_new_dependencies_requirement__without_requirements(
    temporary_app: App,
) -> None:
    plugins = [UpstreamWithoutRequirements.plugin, DownstreamWithoutRequirements.plugin]
    actual = await new_dependencies_requirement(
        UpstreamWithoutRequirements.plugin, plugins, services=temporary_app
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
        UpstreamWithUnmetRequirements.plugin, plugins, services=temporary_app
    )
    assert actual is not None
    message = actual.localize(DEFAULT_LOCALIZER)
    assert "downstream-requirement-summary" in message


async def test_new_dependencies_requirement__with_met_requirements(
    temporary_app: App,
) -> None:
    plugins = [UpstreamWithMetRequirements.plugin, DownstreamWithMetRequirements.plugin]
    actual = await new_dependencies_requirement(
        UpstreamWithMetRequirements.plugin, plugins, services=temporary_app
    )
    assert actual is None


class TestCyclicDependencyError:
    def test(self) -> None:
        plugin_id = "my-first-plugin"
        sut = CyclicDependencyError([plugin_id])
        assert plugin_id in str(sut)


async def test_get_requirement__without_classed_plugin() -> None:
    assert await get_requirement(DummyPluginOne.plugin, None) is None


async def test_get_requirement__without_has_requirement() -> None:
    assert await get_requirement(DummyPluginOne, None) is None


async def test_get_requirement__without_requirement() -> None:
    @DummyPluginDefinition("-")
    class _Plugin(HasRequirement, DummyPlugin):
        pass

    assert await get_requirement(_Plugin, None) is None


async def test_get_requirement__with_requirement() -> None:
    requirement = StaticRequirement("")

    @DummyPluginDefinition("-")
    class _Plugin(HasRequirement, DummyPlugin):
        @override
        @classmethod
        async def requirement(cls, level: ServiceLevel, /) -> Requirement | None:
            return requirement

    assert await get_requirement(_Plugin, None) is requirement


class TestCheckRequirementRepository:
    async def test_get__without_requirement(self) -> None:
        sut = await CheckRequirementRepository.new(
            DummyPluginDefinition, [DummyPluginOne.plugin], None
        )
        assert sut.get(DummyPluginOne.plugin.id) is DummyPluginOne.plugin

    async def test_get__with_plugin_not_found(self) -> None:
        sut = await CheckRequirementRepository.new(DummyPluginDefinition, [], None)
        with pytest.raises(PluginNotFound):
            sut.get("non-existent-plugin")

    async def test_get__with_unmet_requirement(self) -> None:
        sut = await CheckRequirementRepository.new(
            HasRequirementPluginDefinition, [DownstreamWithUnmetRequirements], None
        )
        with pytest.raises(PluginNotFound):
            sut.get("non-existent-plugin")

    async def test___iter____without_requirement(self) -> None:
        sut = await CheckRequirementRepository.new(
            DummyPluginDefinition, [DummyPluginOne.plugin], None
        )
        assert list(iter(sut)) == [DummyPluginOne.plugin]

    async def test___iter____without_plugins(self) -> None:
        sut = await CheckRequirementRepository.new(DummyPluginDefinition, [], None)
        assert not list(iter(sut))

    async def test___iter____with_unmet_requirement(self) -> None:
        sut = await CheckRequirementRepository.new(
            HasRequirementPluginDefinition, [DownstreamWithUnmetRequirements], None
        )
        assert not list(iter(sut))
