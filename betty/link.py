"""
An API for linking to web resources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final, override

from betty.classtools import Singleton
from betty.locale.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import Order, OrderedPluginDefinition

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName


class LinkType(ABC):
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


class Link(Singleton, Plugin["LinkDefinition"]):
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
class LinkDefinition(OrderedPluginDefinition, PluginClsDefinition[Link]):
    """
    .. plugin_type:: link.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order[LinkDefinition] = (),
        before: Order[LinkDefinition] = (),
        link: LinkType,
        primary: bool = False,
    ):
        super().__init__(plugin_id, before=before, after=after)
        self._link = link
        self._primary = primary

    @property
    def link(self) -> LinkType:
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


@final
class StaticLink(LinkType):
    """
    A static link.
    """

    def __init__(self, url: ResolvableLocalizable, label: ResolvableLocalizable):
        self._url = resolve_localizable(url)
        self._label = resolve_localizable(label)

    @override
    @property
    def url(self) -> Localizable:
        return self._url

    @override
    @property
    def label(self) -> Localizable:
        return self._label
