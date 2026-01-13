"""
Configuration for ordered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.assertion import (
    Field,
    OptionalField,
    assert_sequence,
)
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin.config import PluginDefinitionConfiguration
from betty.plugin.resolve import ResolvableId, resolve_id

if TYPE_CHECKING:
    from collections.abc import Collection, MutableSet, Set

    from betty.serde import SerializedData, SerializedMapping


class OrderedPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.plugin.ordered.OrderedPluginDefinition`.

    .. configuration:: betty.plugin.config.ordered:OrderedPluginDefinitionConfiguration
    """

    comes_before: MutableSet[MachineName]
    comes_after: MutableSet[MachineName]

    def __init__(
        self,
        comes_before: Set[ResolvableId] | None = None,
        comes_after: Set[ResolvableId] | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.comes_before = (
            set() if comes_before is None else set(map(resolve_id, comes_before))
        )
        self.comes_after = (
            set() if comes_after is None else set(map(resolve_id, comes_after))
        )

    @override
    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        return [
            *super().fields(),
            OptionalField("comes_before", assert_sequence(assert_machine_name()) | set),
            OptionalField("comes_after", assert_sequence(assert_machine_name()) | set),
        ]

    @override
    def dump(self) -> SerializedMapping[SerializedData]:
        serialized = super().dump()
        if self.comes_before:
            serialized["comes_before"] = list(self.comes_before)
        if self.comes_after:
            serialized["comes_after"] = list(self.comes_after)
        return serialized

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        eq = super().__eq__(other)
        if eq is not True:
            return eq
        return (self.comes_before, self.comes_after) == (
            other.comes_before,
            other.comes_after,
        )
