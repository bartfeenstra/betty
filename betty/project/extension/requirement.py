"""Provide requirements for Betty's extension API."""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Sequence,
)

from typing_extensions import override

from betty.asyncio import wait_to_thread
from betty.locale.localizable import _, Localizable, call
from betty.project import extension
from betty.project.extension import CyclicDependencyError
from betty.requirement import Requirement, AllRequirements

if TYPE_CHECKING:
    from betty.project.extension import Extension


class Dependencies(AllRequirements):
    """
    Check a dependent's dependency requirements.
    """

    def __init__(self, dependent: type[Extension]):
        self._dependent = dependent
        super().__init__(*self._get_requirements())

    def _get_requirements(self) -> Sequence[Requirement]:
        try:
            return [
                (
                    wait_to_thread(
                        extension.EXTENSION_REPOSITORY.get(dependency_identifier)
                    )
                    if isinstance(dependency_identifier, str)
                    else dependency_identifier
                ).enable_requirement()
                for dependency_identifier in self._dependent.depends_on()
            ]
        except RecursionError:
            raise CyclicDependencyError([self._dependent]) from None

    @override
    async def summary(self) -> Localizable:
        return _("{dependent_label} requires {dependency_labels}.").format(
            dependent_label=self._dependent.plugin_label(),
            dependency_labels=call(
                lambda localizer: ", ".join(
                    (
                        wait_to_thread(
                            extension.EXTENSION_REPOSITORY.get(dependency_identifier)
                        )
                        if isinstance(dependency_identifier, str)
                        else dependency_identifier
                    )
                    .plugin_label()
                    .localize(localizer)
                    for dependency_identifier in self._dependent.depends_on()
                ),
            ),
        )


class Dependents(Requirement):
    """
    Check a dependency's dependent requirements.
    """

    def __init__(self, dependency: Extension):
        super().__init__()
        self._dependency = dependency
        self.__dependents: Sequence[Extension] | None = None

    async def _dependents(self) -> Sequence[Extension]:
        if self.__dependents is None:
            self.__dependents = [
                project_extension
                for project_extension in self._dependency.project.extensions.flatten()
                if self._dependency.plugin_id() in project_extension.depends_on()
            ]
        return self.__dependents

    @override
    async def summary(self) -> Localizable:
        return _("{dependency_label} is required by {dependency_labels}.").format(
            dependency_label=self._dependency.plugin_label(),
            dependent_labels=call(
                lambda localizer: ", ".join(
                    dependent.plugin_label().localize(localizer)
                    for dependent in wait_to_thread(self._dependents())
                )
            ),
        )

    @override
    async def is_met(self) -> bool:
        # This class is never instantiated unless there is at least one enabled dependent, which means this requirement
        # is always met.
        return True
