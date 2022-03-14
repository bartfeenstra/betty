from textwrap import indent
from typing import Optional, Iterable, TYPE_CHECKING


if TYPE_CHECKING:
    from betty.builtins import _

from betty.error import UserFacingError


class Requirement:
    @property
    def met(self) -> bool:
        raise NotImplementedError

    def assert_met(self) -> None:
        if not self.met:
            raise RequirementError(self)

    @property
    def summary(self) -> str:
        raise NotImplementedError

    @property
    def details(self) -> Optional[str]:
        return None

    def __str__(self) -> str:
        string = self.summary
        if self.details:
            string += f'\n{"-" * len(self.summary)}'
            string += f'\n{self.details}'
        return string


class _RequirementCollection(Requirement):
    def __init__(self, requirements: Iterable[Requirement]):
        self._requirements = tuple(requirements)

    @property
    def requirements(self) -> Iterable[Requirement]:
        return self._requirements

    def __add__(self, other):
        if not isinstance(other, Requirement):
            raise NotImplementedError
        self._requirements = (*self._requirements, other)
        return self

    def __str__(self) -> str:
        string = super().__str__()
        for requirement in self._requirements:
            string += f'\n-{indent(str(requirement), "  ")[1:]}'
        return string


class AnyRequirement(_RequirementCollection):
    def __init__(self, requirements: Iterable[Requirement]):
        super().__init__(requirements)
        self._summary = _('One or more of these requirements must be met')

    @property
    def requirements(self) -> Iterable[Requirement]:
        return self._requirements

    @property
    def met(self) -> bool:
        for requirement in self._requirements:
            if requirement.met:
                return True
        return False

    @property
    def summary(self) -> str:
        return self._summary


class AllRequirements(_RequirementCollection):
    def __init__(self, requirements: Iterable[Requirement]):
        super().__init__(requirements)
        self._summary = _('All of these requirements must be met')

    @property
    def met(self) -> bool:
        for requirement in self._requirements:
            if not requirement.met:
                return False
        return True

    @property
    def summary(self) -> str:
        return self._summary


class RequirementError(RuntimeError, UserFacingError):
    def __init__(self, requirement: Requirement):
        super().__init__(requirement)
        self._requirement = requirement

    @property
    def requirement(self) -> Requirement:
        return self._requirement


class Requirer:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def requires(cls) -> Requirement:
        raise NotImplementedError
