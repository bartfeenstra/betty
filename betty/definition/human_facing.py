"""
Definitions that are human-facing and provide human-friendly information.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import TypeVar

from betty.locale.localizable.resolve import resolve_localizable

if TYPE_CHECKING:
    from betty.locale.localizable import (
        CountableLocalizable,
        Localizable,
        ResolvableLocalizable,
    )

_BaseClsCoT = TypeVar("_BaseClsCoT", default=object, covariant=True)


class HumanFacingDefinition:
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
        self._label = resolve_localizable(label)
        self._description = (
            None if description is None else resolve_localizable(description)
        )

    @property
    def label(self) -> Localizable:
        """
        The human-readable short label (singular).
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The human-readable long description.
        """
        return self._description


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
        self._label_plural = resolve_localizable(label_plural)
        self._label_countable = label_countable

    @property
    def label_plural(self) -> Localizable:
        """
        The human-readable short label (plural).
        """
        return self._label_plural

    @property
    def label_countable(self) -> CountableLocalizable:
        """
        The human-readable short label (countable).
        """
        return self._label_countable
