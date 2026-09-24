"""
The Jinja test API.
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


class JinjaTest(HasDefinition["JinjaTestDefinition"]):
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
class JinjaTestDefinition(ClsDefinition[JinjaTest], PluginDefinition):
    """
    .. plugin_type:: jinja-test.
    """

    def __init__(
        self,
        jinja_test_plugin: ResolvableMachineName,
        *,
        auto: bool = False,
        requires: Requires = (),
    ):
        super().__init__(jinja_test_plugin, auto=auto, requires=requires)


@final
@NewPluginDefinition(JinjaTestDefinition)
class NewJinjaTest(NewPlugin[JinjaTestDefinition, JinjaTest]):
    """
    The Jinja test factory.
    """
