"""
Definitions that are human-facing and provide human-friendly information.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from betty.definition import Definition
from betty.localizable import resolve_localizable

if TYPE_CHECKING:
    from betty.localizable import (
        CountableLocalizable,
        Localizable,
        ResolvableLocalizable,
    )


class HumanFacingDefinition(Definition):
    """
    A definition that is human-facing and provides human-friendly information.
    """

    def __init__(
        self,
        *args: Any,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.label: Final[Localizable] = resolve_localizable(label)
        """
        The human-readable short label (singular).
        """
        self.description: Final[Localizable | None] = (
            None if description is None else resolve_localizable(description)
        )
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
        label: ResolvableLocalizable,
        label_plural: ResolvableLocalizable,
        label_countable: CountableLocalizable,
        description: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, label=label, description=description, **kwargs)
        self.label_plural: Final[Localizable] = resolve_localizable(label_plural)
        """
        The human-readable short label (plural).
        """
        self.label_countable: Final[CountableLocalizable] = label_countable
        """
        The human-readable short label (countable).
        """
