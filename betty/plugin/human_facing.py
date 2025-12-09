"""
Plugins that are human-facing and have localizable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import TypeVar, override

from betty.locale.localizable.attr import (
    OptionalLocalizableAttr,
    RequiredLocalizableAttr,
)
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.plugin import PluginDefinition

if TYPE_CHECKING:
    from betty.locale.localizable import (
        CountableLocalizable,
        Localizable,
        LocalizableLike,
    )
    from betty.machine_name import MachineName


_BaseClsCoT = TypeVar("_BaseClsCoT", default=object, covariant=True)


class HumanFacingPluginDefinition(PluginDefinition[_BaseClsCoT]):
    """
    A definition of a plugin that is human-facing.
    """

    _label = RequiredLocalizableAttr("_label")
    _description = OptionalLocalizableAttr("_description")

    def __init__(
        self,
        plugin_id: MachineName,
        *,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        **kwargs: Any,
    ):
        super().__init__(plugin_id, **kwargs)
        self._label = label
        self._description = description

    @override
    @property
    def reference_label(self) -> Localizable:
        return _('"{plugin_id}" ({plugin_label})').format(
            plugin_id=self.id,
            plugin_label=self.label,
        )

    @override
    @property
    def reference_label_with_type(self) -> Localizable:
        return _('{plugin_type} "{plugin_id}" ({plugin_label})').format(
            plugin_type=self.type().label,
            plugin_id=self.id,
            plugin_label=self.label,
        )

    @property
    def label(self) -> Localizable:
        """
        The human-readable short plugin label (singular).
        """
        return self._label

    @property
    def description(self) -> Localizable | None:
        """
        The human-readable long plugin description.
        """
        return self._description


class CountableHumanFacingPluginDefinition(HumanFacingPluginDefinition[_BaseClsCoT]):
    """
    A definition of a plugin that is human-facing, and of which instances are countable.
    """

    def __init__(
        self,
        plugin_id: MachineName,
        *,
        label: LocalizableLike,
        label_plural: LocalizableLike,
        label_countable: CountableLocalizable,
        description: LocalizableLike | None = None,
        **kwargs: Any,
    ):
        super().__init__(plugin_id, label=label, description=description, **kwargs)
        self._label_plural = ensure_localizable(label_plural)
        self._label_countable = label_countable

    @property
    def label_plural(self) -> Localizable:
        """
        The human-readable short plugin label (plural).
        """
        return self._label_plural

    @property
    def label_countable(self) -> CountableLocalizable:
        """
        The human-readable short plugin label (countable).
        """
        return self._label_countable
