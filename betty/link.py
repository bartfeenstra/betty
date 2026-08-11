"""
An API for linking to web resources.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Final, final, override

from betty.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import Order, OrderedPluginDefinition

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName


class Link(metaclass=ABCMeta):
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


@final
@PluginTypeDefinition(
    "link",
    label=_("Link"),
    label_plural=_("Links"),
    label_countable=ngettext("{count} link", "{count} links"),
)
class LinkDefinition(OrderedPluginDefinition):
    """
    .. plugin_type:: link.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order[LinkDefinition] = (),
        auto: bool = False,
        before: Order[LinkDefinition] = (),
        link: Link,
        primary: bool = False,
    ):
        super().__init__(plugin_id, before=before, after=after, auto=auto)
        self.link: Final[Link] = link
        """
        The link.
        """
        self.primary: Final[bool] = primary
        """
        Whether this is a primary links or not.
        """


@final
class StaticLink(Link):
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
