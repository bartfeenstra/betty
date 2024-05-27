"""
Provide an API that lets code express arbitrary requirements.
"""

from __future__ import annotations

from textwrap import indent
from typing import cast, Any, Self

from typing_extensions import override

from betty.error import UserFacingError
from betty.locale import Str, Localizable, Localizer


class Requirement(Localizable):
    """
    Express a requirement.
    """

    def is_met(self) -> bool:
        """
        Check if the requirement is met.
        """
        raise NotImplementedError(repr(self))

    def assert_met(self) -> None:
        """
        Assert that the requirement is met.
        """
        if not self.is_met():
            raise RequirementError(self)
        return None

    def summary(self) -> Str:
        """
        Get the requirement's human-readable summary.
        """
        raise NotImplementedError(repr(self))

    def details(self) -> Str | None:
        """
        Get the requirement's human-readable additional details.
        """
        return None

    @override
    def localize(self, localizer: Localizer) -> str:
        string = self.summary().localize(localizer)
        details = self.details()
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


class RequirementError(UserFacingError, RuntimeError):
    """
    Raised when a requirement is not met.
    """

    def __init__(self, requirement: Requirement):
        super().__init__(requirement)
        self._requirement = requirement

    @override
    def __reduce__(self) -> tuple[type[Self], tuple[Requirement]]:
        return type(self), (self._requirement,)

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
        self._requirements: list[Requirement] = [
            requirement for requirement in requirements if requirement
        ]

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self._requirements == other._requirements

    def __add__(self, other: Any) -> Self:
        if not isinstance(other, Requirement):
            raise NotImplementedError(repr(self))
        self._requirements = [*self._requirements, other]
        return self

    @override
    def localize(self, localizer: Localizer) -> str:
        localized = super().localize(localizer)
        for requirement in self._requirements:
            localized += f'\n-{indent(requirement.localize(localizer), "  ")[1:]}'
        return localized

    @override
    def reduce(self) -> Requirement | None:
        reduced_requirements = []
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


class AnyRequirement(RequirementCollection):
    """
    A requirement that is met if any of the given requirements are met.
    """

    def __init__(self, *requirements: Requirement | None):
        super().__init__(*requirements)
        self._summary = Str._("One or more of these requirements must be met")

    @override
    def is_met(self) -> bool:
        return any(requirement.is_met() for requirement in self._requirements)

    @override
    def summary(self) -> Str:
        return self._summary


class AllRequirements(RequirementCollection):
    """
    A requirement that is met if all of the given requirements are met.
    """

    def __init__(self, *requirements: Requirement | None):
        super().__init__(*requirements)
        self._summary = Str._("All of these requirements must be met")

    @override
    def is_met(self) -> bool:
        return all(requirement.is_met() for requirement in self._requirements)

    @override
    def summary(self) -> Str:
        return self._summary
