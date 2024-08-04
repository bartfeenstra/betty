"""
Provide an API that lets code express arbitrary requirements.
"""

from __future__ import annotations

from abc import abstractmethod
from textwrap import indent
from typing import cast, Any, TYPE_CHECKING, final

from betty.asyncio import wait_to_thread
from betty.error import UserFacingError
from betty.locale.localizable import _, Localizable
from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Sequence, MutableSequence
    from betty.locale.localizer import Localizer


class Requirement(Localizable):
    """
    Express a requirement.
    """

    @abstractmethod
    async def is_met(self) -> bool:
        """
        Check if the requirement is met.
        """
        pass

    async def assert_met(self) -> None:
        """
        Assert that the requirement is met.
        """
        if not await self.is_met():
            raise RequirementError(self)
        return None

    @abstractmethod
    async def summary(self) -> Localizable:
        """
        Get the requirement's human-readable summary.
        """
        pass

    async def details(self) -> Localizable | None:
        """
        Get the requirement's human-readable additional details.
        """
        return None

    @override
    def localize(self, localizer: Localizer) -> str:
        string = wait_to_thread(self.summary()).localize(localizer)
        details = wait_to_thread(self.details())
        if details is not None:
            string += f'\n{"-" * len(string)}'
            string += f"\n{details.localize(localizer)}"
        return string

    def reduce(self) -> Requirement | None:
        """
        Remove unnecessary components of this requirement.

        - Collections can flatten unnecessary hierarchies.
        - Empty decorators or collections can 'dissolve' themselves and return None.

        This function MUST NOT modify self.
        """
        return self


@final
class RequirementError(UserFacingError, RuntimeError):
    """
    Raised when a requirement is not met.
    """

    def __init__(self, requirement: Requirement):
        super().__init__(requirement)
        self._requirement = requirement

    def requirement(self) -> Requirement:
        """
        Get the requirement this error is for.
        """
        return self._requirement


class RequirementCollection(Requirement):
    """
    Provide a collection of zero or more requirements.
    """

    def __init__(self, *requirements: Requirement | None):
        super().__init__()
        self._requirements: Sequence[Requirement] = [
            requirement for requirement in requirements if requirement
        ]

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self._requirements == other._requirements

    @override
    def localize(self, localizer: Localizer) -> str:
        localized = super().localize(localizer)
        for requirement in self._requirements:
            localized += f'\n-{indent(requirement.localize(localizer), "  ")[1:]}'
        return localized

    @override
    def reduce(self) -> Requirement | None:
        reduced_requirements: MutableSequence[Requirement] = []
        for requirement in self._requirements:
            reduced_requirement = requirement.reduce()
            if reduced_requirement:
                if type(reduced_requirement) is type(self):
                    reduced_requirements.extend(
                        cast(RequirementCollection, reduced_requirement)._requirements
                    )
                else:
                    reduced_requirements.append(reduced_requirement)
        if len(reduced_requirements) == 1:
            return reduced_requirements[0]
        if reduced_requirements:
            return type(self)(*reduced_requirements)
        return None


@final
class AnyRequirement(RequirementCollection):
    """
    A requirement that is met if any of the given requirements are met.
    """

    def __init__(self, *requirements: Requirement | None):
        super().__init__(*requirements)
        self._summary = _("One or more of these requirements must be met")

    @override
    async def is_met(self) -> bool:
        return any([await requirement.is_met() for requirement in self._requirements])

    @override
    async def summary(self) -> Localizable:
        return self._summary


class AllRequirements(RequirementCollection):
    """
    A requirement that is met if all of the given requirements are met.
    """

    def __init__(self, *requirements: Requirement | None):
        super().__init__(*requirements)
        self._summary = _("All of these requirements must be met")

    @override
    async def is_met(self) -> bool:
        return all([await requirement.is_met() for requirement in self._requirements])

    @override
    async def summary(self) -> Localizable:
        return self._summary
