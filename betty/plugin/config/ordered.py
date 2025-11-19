"""
Configuration for ordered plugins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    assert_fields,
    assert_mapping,
    assert_sequence,
    assert_setattr,
)
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin import PluginIdentifier, resolve_id
from betty.plugin.config import PluginDefinitionConfiguration

if TYPE_CHECKING:
    from collections.abc import MutableSet, Set

    from betty.serde.dump import Dump, DumpMapping


class OrderedPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.plugin.ordered.OrderedPluginDefinition`.
    """

    comes_before: MutableSet[MachineName]
    comes_after: MutableSet[MachineName]

    def __init__(
        self,
        comes_before: Set[PluginIdentifier] | None = None,
        comes_after: Set[PluginIdentifier] | None = None,
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
    def load(self, dump: Dump) -> None:
        self.assert_mutable()

        mapping = assert_mapping()(dump)
        assert_fields(
            OptionalField(
                "comes_before",
                assert_sequence(assert_machine_name())
                | set
                | assert_setattr(self, "comes_before"),
            ),
            OptionalField(
                "comes_after",
                assert_sequence(assert_machine_name())
                | set
                | assert_setattr(self, "comes_after"),
            ),
        )(mapping)
        mapping.pop("comes_before", None)
        mapping.pop("comes_after", None)
        super().load(mapping)

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump = super().dump()
        if self.comes_before:
            dump["comes_before"] = list(self.comes_before)
        if self.comes_after:
            dump["comes_after"] = list(self.comes_after)
        return dump
