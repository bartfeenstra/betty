"""
Provide an API that lets code express arbitrary requirements.
"""

from __future__ import annotations

from abc import abstractmethod
from textwrap import indent
from typing import TYPE_CHECKING, Any, cast, final

from typing_extensions import override

from betty.error import UserFacingError
from betty.locale.localizable import Localizable, _
from betty.locale.localized import LocalizedStr

if TYPE_CHECKING:
    from collections.abc import MutableSequence, Sequence

    from betty.locale.localizer import Localizer


class Requirement(Localizable):
    """
    Express a requirement.
    """

    @abstractmethod
    def is_met(self) -> bool:
        """
        Check if the requirement is met.
        """

    def assert_met(self) -> None:
        """
        Assert that the requirement is met.
        """
        if not self.is_met():
            raise RequirementError(self)
        return

    @abstractmethod
    def summary(self) -> Localizable:
        """
        Get the requirement's human-readable summary.
        """

    def details(self) -> Localizable | None:
        """
        Get the requirement's human-readable additional details.
        """
        return None

    @override
    def localize(self, localizer: Localizer) -> LocalizedStr:
        super_localized = self.summary().localize(localizer)
        details = self.details()
        localized: str = super_localized
        if details is not None:
            localized += f"\n{'-' * len(localized)}"
            localized += f"\n{details.localize(localizer)}"
        return LocalizedStr(localized, locale=super_localized.locale)

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
    def localize(self, localizer: Localizer) -> LocalizedStr:
        super_localized = super().localize(localizer)
        localized: str = super_localized
        for requirement in self._requirements:
            localized += f"\n-{indent(requirement.localize(localizer), '  ')[1:]}"
        return LocalizedStr(localized, locale=super_localized.locale)

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
    def is_met(self) -> bool:
        return any(requirement.is_met() for requirement in self._requirements)

    @override
    def summary(self) -> Localizable:
        return self._summary


class AllRequirements(RequirementCollection):
    """
    A requirement that is met if all of the given requirements are met.
    """

    def __init__(self, *requirements: Requirement | None):
        super().__init__(*requirements)
        self._summary = _("All of these requirements must be met")

    @override
    def is_met(self) -> bool:
        return all(requirement.is_met() for requirement in self._requirements)

    @override
    def summary(self) -> Localizable:
        return self._summary
