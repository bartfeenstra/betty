"""
The Jinja filter API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.definition import HasDefinition
from betty.definition.cls import ClsDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.cls.factory import NewPlugin, NewPluginDefinition

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class JinjaFilter(HasDefinition["JinjaFilterDefinition"]):
    """
    A Jinja filter.

    Subclasses **MUST** have a ``.__call__()`` method of any signature.
    """


@final
@PluginTypeDefinition(
    "jinja-filter",
    label=_("Jinja filter"),
    label_plural=_("Jinja filters"),
    label_countable=ngettext("{count} Jinja filter", "{count} Jinja filters"),
)
class JinjaFilterDefinition(ClsDefinition[JinjaFilter], PluginDefinition):
    """
    .. plugin_type:: jinja-filter.
    """

    def __init__(
        self,
        jinja_filter_id: ResolvableMachineName,
        *,
        auto: bool = False,
        requires: Requires = (),
    ):
        super().__init__(jinja_filter_id, auto=auto, requires=requires)


@final
@NewPluginDefinition(JinjaFilterDefinition)
class NewJinjaFilter(NewPlugin[JinjaFilterDefinition, JinjaFilter]):
    """
    The Jinja filter factory.
    """
