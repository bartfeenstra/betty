"""
Definitions that are human-facing and provide human-friendly information.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, final, override

from betty.definition import Definition

if TYPE_CHECKING:
    from betty.localizable import CountableLocalizable
    from betty.localizer import AnyLocalizable


class HumanFacingDefinition(Definition, metaclass=ABCMeta):
    """
    A definition that is human-facing and provides human-friendly information.
    """

    @property
    @abstractmethod
    def label(self) -> AnyLocalizable:
        """
        The human-readable short label (singular).
        """

    @property
    @abstractmethod
    def description(self) -> AnyLocalizable | None:
        """
        The human-readable long description.
        """


class HumanFacingDefinitionBase(HumanFacingDefinition):
    """
    A base class for :py:class:`betty.definition.human_facing.HumanFacingDefinition`.
    """

    def __init__(
        self,
        *args: Any,
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.__label = label
        self.__description = description

    @final
    @override
    def label(self) -> AnyLocalizable:
        return self.__label

    @final
    @override
    def description(self) -> AnyLocalizable | None:
        return self.__description


class CountableHumanFacingDefinition(HumanFacingDefinition):
    """
    A definition that is human-facing and provides countable human-friendly information.
    """

    @property
    @abstractmethod
    def label_plural(self) -> AnyLocalizable:
        """
        The human-readable short label (plural).
        """

    @property
    @abstractmethod
    def label_countable(self) -> CountableLocalizable:
        """
        The human-readable short label (countable).
        """


class CountableHumanFacingDefinitionBase(
    HumanFacingDefinitionBase, CountableHumanFacingDefinition
):
    """
    A base class for :py:class:`betty.definition.human_facing.CountableHumanFacingDefinition`.
    """

    def __init__(
        self,
        *args: Any,
        label: AnyLocalizable,
        label_plural: AnyLocalizable,
        label_countable: CountableLocalizable,
        description: AnyLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, label=label, description=description, **kwargs)
        self.__label_plural = label_plural
        self.__label_countable = label_countable

    @final
    @override
    def label_plural(self) -> AnyLocalizable:
        return self.__label_plural

    @final
    @override
    def label_countable(self) -> CountableLocalizable:
        return self.__label_countable
