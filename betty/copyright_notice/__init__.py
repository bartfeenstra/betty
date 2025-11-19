"""
Provide copyright notices.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar, final

from betty.locale.localizable import _
from betty.mutability import Mutable
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    HumanFacingPluginDefinition,
    PluginTypeDefinition,
)
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable


class CopyrightNotice(Mutable, ClassedPlugin):
    """
    A copyright notice.

    Read more about :doc:`/development/plugin/copyright-notice`.

    To test your own subclasses, use :py:class:`betty.test_utils.copyright_notice.CopyrightNoticeTestBase`.
    """

    plugin: ClassVar[CopyrightNoticeDefinition]

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
class CopyrightNoticeDefinition(
    HumanFacingPluginDefinition, ClassedPluginDefinition[CopyrightNotice]
):
    """
    A copyright notice definition.

    Read more about :doc:`/development/plugin/copyright-notice`.
    """

    plugin_type_cls = CopyrightNotice
    type = PluginTypeDefinition(
        id="copyright-notice",
        label=_("Copyright notice"),
        discoveries=[
            EntryPointDiscovery("betty.copyright_notice"),
            ProjectDiscovery(
                lambda project: project.configuration.copyright_notices.new_plugins()
            ),
        ],
    )
