from __future__ import annotations

from textwrap import indent
from typing import Optional, cast, List, Any

from betty.error import UserFacingError
from betty.locale import Localizer, Localizable


class Requirement(Localizable):
    def is_met(self) -> bool:
        raise NotImplementedError(repr(self))

    def assert_met(self) -> None:
        if not self.is_met():
            raise RequirementError(self)
        return None

    def summary(self) -> str:
        raise NotImplementedError(repr(self))

    def details(self) -> Optional[str]:
        return None

    def __str__(self) -> str:
        string = self.summary()
        if self.details():
            string += f'\n{"-" * len(self.summary())}'
            string += f'\n{self.details()}'
        return string

    def reduce(self) -> Optional[Requirement]:
        """
        Removes unnecessary components of this requirement.
        - Collections can flatten unnecessary hierarchies.
        - Empty decorators or collections can 'dissolve' themselves and return None.

        This function MUST NOT modify self.
        """
        return self


class RequirementError(RuntimeError, UserFacingError):
    def __init__(self, requirement: Requirement):
        super().__init__(str(requirement))
        self._requirement = requirement

    def requirement(self) -> Requirement:
        return self._requirement


class RequirementCollection(Requirement):
    def __init__(self, *requirements: Optional[Requirement], localizer: Localizer | None = None):
        super().__init__(localizer=localizer)
        self._requirements: List[Requirement] = [requirement for requirement in requirements if requirement]

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self._requirements == other._requirements

    def __add__(self, other):
        if not isinstance(other, Requirement):
            raise NotImplementedError(repr(self))
        self._requirements = [*self._requirements, other]
        return self

    def __str__(self) -> str:
        string = super().__str__()
        for requirement in self._requirements:
            string += f'\n-{indent(str(requirement), "  ")[1:]}'
        return string

    def reduce(self) -> Optional[Requirement]:
        reduced_requirements = []
        for requirement in self._requirements:
            requirement = requirement.reduce()  # type: ignore
            if requirement:
                if type(requirement) == type(self):
                    reduced_requirements.extend(cast(RequirementCollection, requirement)._requirements)
                else:
                    reduced_requirements.append(requirement)
        if len(reduced_requirements) == 1:
            return reduced_requirements[0]
        if reduced_requirements:
            return type(self)(*reduced_requirements)
        return None


class AnyRequirement(RequirementCollection):
    def __init__(self, *requirements: Optional[Requirement], localizer: Localizer | None = None):
        super().__init__(*requirements, localizer=localizer)
        self._summary = self.localizer._('One or more of these requirements must be met')

    def is_met(self) -> bool:
        for requirement in self._requirements:
            if requirement.is_met():
                return True
        return False

    def summary(self) -> str:
        return self._summary


class AllRequirements(RequirementCollection):
    def __init__(self, *requirements: Optional[Requirement], localizer: Localizer | None = None):
        super().__init__(*requirements, localizer=localizer)
        self._summary = self.localizer._('All of these requirements must be met')

    def is_met(self) -> bool:
        for requirement in self._requirements:
            if not requirement.is_met():
                return False
        return True

    def summary(self) -> str:
        return self._summary
