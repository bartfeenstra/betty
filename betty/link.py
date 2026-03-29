"""
An API for linking to web resources.
"""

from abc import abstractmethod
from typing import Any, Protocol, final, override

from betty.locale.localizable import Localizable
from betty.locale.localizable.gettext import _, ngettext
from betty.machine_name import ResolvableMachineName
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import Order, OrderedPluginDefinition
from betty.plugin.service import ServicePluginDefinition


class LinkType(Protocol):
    """
    A link to a web resource.
    """

    @property
    @abstractmethod
    def url(self) -> Localizable:
        """
        The URL the link points to.
        """

    @property
    @abstractmethod
    def label(self) -> Localizable:
        """
        The human-readable short link label.
        """


class Link(Plugin["LinkDefinition"]):
    """
    A link to a web resource.
    """


@final
@PluginTypeDefinition(
    "link",
    label=_("Link"),
    label_plural=_("Links"),
    label_countable=ngettext("{count} link", "{count} links"),
)
class LinkDefinition(OrderedPluginDefinition, ServicePluginDefinition[Link]):
    """
    .. plugin_type:: link.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order[OrderedPluginDefinition[Link]] | None = None,
        before: Order[OrderedPluginDefinition[Link]] | None = None,
        link: LinkType,
        primary: bool = False,
    ):
        super().__init__(plugin_id, before=before, after=after)
        self._link = link
        self._primary = primary

    @property
    def link(self) -> Any:
        """
        The link.
        """
        return self._link

    @property
    def primary(self) -> bool:
        """
        Whether this is a primary links or not.
        """
        return self._primary


@final
class LinkManufacturer(PluginManufacturer[LinkDefinition, Link]):
    """
    The link manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[LinkDefinition]:
        return LinkDefinition
