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

    from betty.serde.dump import Dump, DumpMapping


class OrderedPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.plugin.ordered.OrderedPluginDefinition`.
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
    def dump(self) -> DumpMapping[Dump]:
        dump = super().dump()
        if self.comes_before:
            dump["comes_before"] = list(self.comes_before)
        if self.comes_after:
            dump["comes_after"] = list(self.comes_after)
        return dump
