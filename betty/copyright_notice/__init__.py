"""
Provide copyright notices.
"""

from abc import abstractmethod

from betty.locale.localizable import Localizable
from betty.mutability import Mutable
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository


class CopyrightNotice(Mutable, Plugin):
    """
    A copyright notice.

    Read more about :doc:`/development/plugin/copyright-notice`.

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


COPYRIGHT_NOTICE_REPOSITORY: PluginRepository[CopyrightNotice] = (
    EntryPointPluginRepository("betty.copyright_notice")
)
"""
The copyright notice plugin repository.

Read more about :doc:`/development/plugin/copyright-notice`.
"""
