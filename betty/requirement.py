"""
Provide an API that lets code express arbitrary requirements.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.exception import HumanFacingException
from betty.locale.localizable import Localizable, LocalizableLike
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Lines, UnorderedList

if TYPE_CHECKING:
    from collections.abc import MutableSequence, Sequence

    from betty.locale import HasLocale
    from betty.locale.localize import Localizer
    from betty.service.level import ServiceLevel


class Requirement(Localizable):
    """
    Express a requirement.
    """

    @property
    @abstractmethod
    def summary(self) -> Localizable:
        """
        Get the requirement's human-readable summary.
        """

    @property
    def details(self) -> Localizable | None:
        """
        Get the requirement's human-readable additional details.
        """
        return None

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        localized = self.summary.localize(localizer)
        details = self.details
        if details is None:
            return localized
        return Lines(self.summary, "-" * len(localized), details).localize(localizer)


class UnmetRequirement(HumanFacingException, RuntimeError):
    """
    Raised when a requirement is not met.
    """

    def __init__(self, requirement: Requirement, *, summary: Localizable | None = None):
        message = requirement if summary is None else Lines(requirement, summary)
        super().__init__(message)
        self._requirement = requirement

    def requirement(self) -> Requirement:
        """
        Get the requirement this error is for.
        """
        return self._requirement


class _RequirementCollection(Requirement, ABC):
    _DEFAULT_SUMMARY: Localizable

    def __init__(
        self, *requirements: Requirement, summary: LocalizableLike | None = None
    ):
        super().__init__()
        assert len(requirements)
        self._requirements: MutableSequence[Requirement] = []
        for requirement in requirements:
            if isinstance(requirement, type(self)):
                for nested_requirement in requirement._requirements:
                    self._requirements.append(nested_requirement)
            else:
                self._requirements.append(requirement)
        self._summary = (
            self._DEFAULT_SUMMARY if summary is None else ensure_localizable(summary)
        )

    @classmethod
    @abstractmethod
    def _filter(
        cls, requirements: Sequence[Requirement | None]
    ) -> Sequence[Requirement]:
        pass

    @classmethod
    def new(
        cls, *requirements: Requirement | None, summary: LocalizableLike | None = None
    ) -> Requirement | None:
        requirements = cls._filter(requirements)
        if not requirements:
            return None
        if len(requirements) == 1:
            return requirements[0]
        return cls(*requirements, summary=summary)

    @override
    @property
    def summary(self) -> Localizable:
        return self._summary

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        return Lines(
            super().localize(localizer),
            UnorderedList(*self._requirements),
        ).localize(localizer)


@final
class AnyRequirement(_RequirementCollection):
    """
    A requirement that requires any of the contained requirements to be met.
    """

    _DEFAULT_SUMMARY = _("One or more of these requirements must be met")

    @override
    @classmethod
    def _filter(
        cls, requirements: Sequence[Requirement | None]
    ) -> Sequence[Requirement]:
        if None in requirements:
            return []
        return list(filter(None, requirements))


@final
class AllRequirements(_RequirementCollection):
    """
    A requirement that requires all of the contained requirements to be met.
    """

    _DEFAULT_SUMMARY = _("All of these requirements must be met")

    @override
    @classmethod
    def _filter(
        cls, requirements: Sequence[Requirement | None]
    ) -> Sequence[Requirement]:
        for requirement in requirements:
            if requirement is not None:
                return list(filter(None, requirements))
        return []


@final
class StaticRequirement(Requirement):
    """
    A simple unmet requirement with static information.
    """

    def __init__(
        self, summary: LocalizableLike, details: LocalizableLike | None = None, /
    ):
        self._summary = ensure_localizable(summary)
        self._details = None if details is None else ensure_localizable(details)

    @property
    @override
    def summary(self) -> Localizable:
        return self._summary

    @property
    @override
    def details(self) -> Localizable | None:
        return self._details


class HasRequirement(ABC):
    """
    Define a class that has requirements to be met before it can be used.
    """

    @classmethod
    @abstractmethod
    async def requirement(cls, services: ServiceLevel, /) -> Requirement | None:
        """
        Define the requirement for this class to be used.
        """
        return None
