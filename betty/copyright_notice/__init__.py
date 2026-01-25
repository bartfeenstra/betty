"""
Provide copyright notices.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable


class CopyrightNotice(Plugin["CopyrightNoticeDefinition"]):
    """
    A copyright notice.

    To test your own subclasses, use :py:class:`betty.test_utils.copyright_notice.CopyrightNoticeTestBase`.
    """

    @property
    @abstractmethod
    def summary(self) -> Localizable:
        """
        The copyright summary.
        """

    @property
    @abstractmethod
    def text(self) -> Localizable:
        """
        The full copyright text.
        """

    @property
    def url(self) -> Localizable | None:
        """
        The URL to an external human-readable resource with more information about this copyright.
        """
        return None


@final
@PluginTypeDefinition(
    "copyright-notice",
    base_cls=CopyrightNotice,
    label=_("Copyright notice"),
    label_plural=_("Copyright notices"),
    label_countable=ngettext("{count} copyright notice", "{count} copyright notices"),
    discovery=[
        EntryPointDiscovery("betty.copyright_notice"),
        ProjectDiscovery(
            lambda project: project.configuration.copyright_notices.new_plugins()
        ),
    ],
)
class CopyrightNoticeDefinition(
    HumanFacingDefinition, PluginDefinition[CopyrightNotice]
):
    """
    .. plugin_type:: copyright-notice.
    """
