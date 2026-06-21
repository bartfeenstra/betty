"""
The Jinja test API.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, final

from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class JinjaTest(Plugin["JinjaTestDefinition"], ABC):
    """
    A Jinja test.

    Subclasses **MUST** have a synchronous ``__call__()`` method that returns a boolean, and takes one or more arguments.
    """


@final
@PluginTypeDefinition(
    "jinja-test",
    label=_("Jinja test"),
    label_plural=_("Jinja tests"),
    label_countable=ngettext("{count} Jinja test", "{count} Jinja tests"),
)
class JinjaTestDefinition(PluginClsDefinition[JinjaTest]):
    """
    .. plugin_type:: jinja-test.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        auto: bool = False,
        requires: Requires = (),
    ):
        super().__init__(plugin_id, auto=auto, requires=requires)


@final
@PluginManufacturerDefinition(JinjaTestDefinition)
class JinjaTestManufacturer(PluginManufacturer[JinjaTestDefinition, JinjaTest]):
    """
    The Jinja test manufacturer.
    """
