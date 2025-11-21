from __future__ import annotations

from typing_extensions import override

from betty.locale.localizable import Localizable, Plain, _
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.requirement import (
    AllRequirements,
    AnyRequirement,
    Requirement,
    StaticRequirement,
    UnmetRequirement,
)


class TestRequirement:
    async def test_localize__without_details(self) -> None:
        class _Requirement(Requirement):
            @override
            @property
            def summary(self) -> Localizable:
                return _("Dolor sit amet")

        assert _Requirement().localize(DEFAULT_LOCALIZER) == "Dolor sit amet"

    async def test_localize__with_details(self) -> None:
        class _Requirement(Requirement):
            @override
            @property
            def summary(self) -> Localizable:
                return _("Dolor sit summary")

            @override
            @property
            def details(self) -> Localizable:
                return _("Dolor sit details")

        assert (
            _Requirement().localize(DEFAULT_LOCALIZER)
            == "Dolor sit summary\n-----------------\nDolor sit details"
        )


class TestAnyRequirement:
    async def test_new__without_met(self) -> None:
        assert AnyRequirement.new(None, None, None) is None

    async def test_new__with_partial_met(self) -> None:
        assert AnyRequirement.new(None, None, StaticRequirement(Plain(""))) is None

    async def test_new__with_all_met(self) -> None:
        assert AnyRequirement.new(None, None, None) is None

    async def test_new__with_nested(self) -> None:
        sut = AnyRequirement.new(
            AnyRequirement.new(
                StaticRequirement(Plain("My first nested requirement")),
                StaticRequirement(Plain("My second nested requirement")),
            )
        )
        assert sut is not None
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "One or more of these requirements must be met\n- My first nested requirement\n- My second nested requirement"
        )

    async def test_summary(self) -> None:
        summary = Plain("")
        requirement = AnyRequirement.new(
            StaticRequirement(Plain("")), StaticRequirement(Plain("")), summary=summary
        )
        assert requirement is not None
        assert requirement.summary is summary

    async def test_summary__default(self) -> None:
        assert AnyRequirement(StaticRequirement(Plain(""))).summary.localize(
            DEFAULT_LOCALIZER
        )


class TestAllRequirements:
    async def test_new__without_met(self) -> None:
        assert AllRequirements.new(None, None, None) is None

    async def test_new__with_partial_met(self) -> None:
        assert AllRequirements.new(None, None, StaticRequirement(Plain(""))) is not None

    async def test_new__with_all_met(self) -> None:
        assert AllRequirements.new(None, None, None) is None

    async def test_new__with_nested(self) -> None:
        sut = AllRequirements.new(
            AllRequirements.new(
                StaticRequirement(Plain("My first nested requirement")),
                StaticRequirement(Plain("My second nested requirement")),
            )
        )
        assert sut is not None
        assert (
            sut.localize(DEFAULT_LOCALIZER)
            == "All of these requirements must be met\n- My first nested requirement\n- My second nested requirement"
        )

    async def test_summary(self) -> None:
        summary = Plain("")
        requirement = AllRequirements.new(
            StaticRequirement(Plain("")), StaticRequirement(Plain("")), summary=summary
        )
        assert requirement is not None
        assert requirement.summary is summary

    async def test_summary__default(self) -> None:
        assert AllRequirements(StaticRequirement(Plain(""))).summary.localize(
            DEFAULT_LOCALIZER
        )


class TestUnmetRequirement:
    def test_requirement(self) -> None:
        requirement = StaticRequirement(Plain(""))
        sut = UnmetRequirement(requirement)
        assert sut.requirement() is requirement


class TestStaticRequirement:
    def test_summary(self) -> None:
        summary = Plain("Hello, world!")
        assert StaticRequirement(summary).summary is summary

    def test_details(self) -> None:
        details = Plain("Hello, world!")
        assert StaticRequirement(Plain(""), details).details is details
