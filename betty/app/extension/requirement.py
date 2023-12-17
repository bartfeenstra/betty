from __future__ import annotations

from textwrap import indent
from typing import cast, Any, Self

from betty.error import UserFacingError
from betty.locale import Str, Localizable, Localizer


class Requirement(Localizable):
    def is_met(self) -> bool:
        raise NotImplementedError(repr(self))

    def assert_met(self) -> None:
        if not self.is_met():
            raise RequirementError(self)
        return None

    def summary(self) -> Str:
        raise NotImplementedError(repr(self))

    def details(self) -> Str | None:
        return None

    def localize(self, localizer: Localizer) -> str:
        string = self.summary().localize(localizer)
        details = self.details()
        if details is not None:
            string += f'\n{"-" * len(string)}'
            string += f'\n{details.localize(localizer)}'
        return string

    def reduce(self) -> Requirement | None:
        """
        Removes unnecessary components of this requirement.
        - Collections can flatten unnecessary hierarchies.
        - Empty decorators or collections can 'dissolve' themselves and return None.

        This function MUST NOT modify self.
        """
        return self


class RequirementError(RuntimeError, UserFacingError):
    def __init__(self, requirement: Requirement):
        super().__init__(requirement)
        self._requirement = requirement

    def requirement(self) -> Requirement:
        return self._requirement


class RequirementCollection(Requirement):
    def __init__(self, *requirements: Requirement | None):
        super().__init__()
        self._requirements: list[Requirement] = [requirement for requirement in requirements if requirement]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self._requirements == other._requirements

    def __add__(self, other: Any) -> Self:
        if not isinstance(other, Requirement):
            raise NotImplementedError(repr(self))
        self._requirements = [*self._requirements, other]
        return self

    def localize(self, localizer: Localizer) -> str:
        localized = super().localize(localizer)
        for requirement in self._requirements:
            localized += f'\n-{indent(requirement.localize(localizer), "  ")[1:]}'
        return localized

    def reduce(self) -> Requirement | None:
        reduced_requirements = []
        for requirement in self._requirements:
            reduced_requirement = requirement.reduce()
            if reduced_requirement:
                if type(reduced_requirement) is type(self):
                    reduced_requirements.extend(cast(RequirementCollection, reduced_requirement)._requirements)
                else:
                    reduced_requirements.append(reduced_requirement)
        if len(reduced_requirements) == 1:
            return reduced_requirements[0]
        if reduced_requirements:
            return type(self)(*reduced_requirements)
        return None


class AnyRequirement(RequirementCollection):
    def __init__(self, *requirements: Requirement | None):
        super().__init__(*requirements)
        self._summary = Str._('One or more of these requirements must be met')

    def is_met(self) -> bool:
        for requirement in self._requirements:
            if requirement.is_met():
                return True
        return False

    def summary(self) -> Str:
        return self._summary


class AllRequirements(RequirementCollection):
    def __init__(self, *requirements: Requirement | None):
        super().__init__(*requirements)
        self._summary = Str._('All of these requirements must be met')

    def is_met(self) -> bool:
        for requirement in self._requirements:
            if not requirement.is_met():
                return False
        return True

    def summary(self) -> Str:
        return self._summary
