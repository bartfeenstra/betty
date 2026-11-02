"""
Definitions that are human-facing and provide human-friendly information.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from betty.definition import Definition

if TYPE_CHECKING:
    from betty.localizable import CountableLocalizable
    from betty.localizer import AnyLocalizable


class HumanFacingDefinition(Definition):
    """
    A definition that is human-facing and provides human-friendly information.
    """

    def __init__(
        self,
        *args: Any,
        label: AnyLocalizable,
        description: AnyLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.label: Final[AnyLocalizable] = label
        """
        The human-readable short label (singular).
        """
        self.description: Final[AnyLocalizable | None] = description
        """
        The human-readable long description.
        """


class CountableHumanFacingDefinition(HumanFacingDefinition):
    """
    A definition that is human-facing and provides countable human-friendly information.
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
        self.label_plural: Final[AnyLocalizable] = label_plural
        """
        The human-readable short label (plural).
        """
        self.label_countable: Final[CountableLocalizable] = label_countable
        """
        The human-readable short label (countable).
        """
