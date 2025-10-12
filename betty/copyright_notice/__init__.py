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
    ClassedPluginTypeDefinition,
    UserFacingPluginDefinition,
)

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
    UserFacingPluginDefinition, ClassedPluginDefinition[CopyrightNotice]
):
    """
    A copyright notice definition.

    Read more about :doc:`/development/plugin/copyright-notice`.
    """

    type: ClassVar[ClassedPluginTypeDefinition] = ClassedPluginTypeDefinition(
        id="copyright-notice",
        label=_("Copyright notice"),
        cls=CopyrightNotice,
    )
