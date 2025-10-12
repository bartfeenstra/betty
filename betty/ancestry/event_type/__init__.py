"""
Provide Betty's ancestry event types.
"""

from __future__ import annotations

from typing import Any, ClassVar, final

from betty.locale.localizable import _
from betty.mutability import Mutable
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    ClassedPluginTypeDefinition,
    OrderedPluginDefinition,
    UserFacingPluginDefinition,
)


class EventType(Mutable, ClassedPlugin):
    """
    Define an :py:class:`betty.ancestry.event.Event` type.
    """

    plugin: ClassVar[EventTypeDefinition]


@final
class EventTypeDefinition(
    UserFacingPluginDefinition,
    OrderedPluginDefinition,
    ClassedPluginDefinition[EventType],
):
    """
    An event type definition.

    Read more about :doc:`/development/plugin/event-type`.
    """

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="event-type",
        label=_("Event type"),
        cls=EventType,
    )

    def __init__(
        self,
        *,
        is_start_of_life: bool = False,
        is_end_of_life: bool = False,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self._is_start_of_life = is_start_of_life
        self._is_end_of_life = is_end_of_life

    @property
    def is_start_of_life(self) -> bool:
        """
        Whether events of this type indicate the start of a person's life.
        """
        return self._is_start_of_life

    @property
    def is_end_of_life(self) -> bool:
        """
        Whether events of this type indicate the end of a person's life.
        """
        return self._is_end_of_life
