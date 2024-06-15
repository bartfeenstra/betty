"""
Provide plugin configuration.
"""

from collections.abc import Sequence
from typing import Self, TypeVar, Generic

from typing_extensions import override

from betty.assertion import (
    RequiredField,
    assert_str,
    assert_record,
    OptionalField,
    assert_setattr,
    assert_mapping,
)
from betty.config import Configuration
from betty.config.collections.mapping import ConfigurationMapping
from betty.locale.localizable import ShorthandStaticTranslations
from betty.locale.localizable.config import (
    StaticTranslationsLocalizableConfigurationAttr,
)
from betty.machine_name import assert_machine_name, MachineName
from betty.plugin import Plugin
from betty.serde.dump import Dump, minimize, VoidableDump

_PluginCoT = TypeVar("_PluginCoT", bound=Plugin, covariant=True)


class PluginConfiguration(Configuration):
    """
    Configure a single plugin.
    """

    label = StaticTranslationsLocalizableConfigurationAttr("label")
    description = StaticTranslationsLocalizableConfigurationAttr(
        "description", required=False
    )

    def __init__(
        self,
        plugin_id: MachineName,
        label: ShorthandStaticTranslations,
        *,
        description: ShorthandStaticTranslations | None = None,
    ):
        super().__init__()
        self._id = assert_machine_name()(plugin_id)
        self.label = label
        if description is not None:
            self.description = description

    @property
    def id(self) -> str:
        """
        The configured plugin ID.
        """
        return self._id

    @override
    def update(self, other: Self) -> None:
        self._id = other.id
        self.label.update(other.label)
        self.description.update(other.description)

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("id", assert_machine_name() | assert_setattr(self, "_id")),
            RequiredField("label", self.label.load),
            OptionalField("description", self.description.load),
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return minimize(
            {
                "id": self.id,
                "label": self.label.dump(),
                "description": self.description.dump(),
            }
        )


_PluginConfigurationT = TypeVar("_PluginConfigurationT", bound=PluginConfiguration)


class PluginConfigurationMapping(
    ConfigurationMapping[str, _PluginConfigurationT],
    Generic[_PluginCoT, _PluginConfigurationT],
):
    """
    Configure a collection of plugins.
    """

    @property
    def plugins(self) -> Sequence[type[_PluginCoT]]:
        """
        The plugins for this configuration.

        You SHOULD NOT cache the value anywhere, as it *will* change
        when this configuration changes.
        """
        return tuple(
            self._create_plugin(plugin_configuration)
            for plugin_configuration in self.values()
        )

    def _create_plugin(self, configuration: _PluginConfigurationT) -> type[_PluginCoT]:
        """
        The plugin (class) for the given configuration.
        """
        raise NotImplementedError

    @override
    def _minimize_item_dump(self) -> bool:
        return True

    @override
    def _get_key(self, configuration: _PluginConfigurationT) -> str:
        return configuration.id

    @override
    @classmethod
    def _load_key(cls, item_dump: Dump, key_dump: str) -> Dump:
        dump_mapping = assert_mapping()(item_dump)
        assert_str()(key_dump)
        dump_mapping["id"] = key_dump
        return dump_mapping

    @override
    def _dump_key(self, item_dump: VoidableDump) -> tuple[VoidableDump, str]:
        dump_mapping = assert_mapping()(item_dump)
        return dump_mapping, dump_mapping.pop("id")


class PluginConfigurationPluginConfigurationMapping(
    PluginConfigurationMapping[_PluginCoT, PluginConfiguration], Generic[_PluginCoT]
):
    """
    Configure a collection of plugins using :py:class:`betty.plugin.config.PluginConfiguration`.
    """

    @override
    def load_item(self, dump: Dump) -> PluginConfiguration:
        item = PluginConfiguration("-", "")
        item.load(dump)
        return item

    @classmethod
    def _create_default_item(cls, configuration_key: str) -> PluginConfiguration:
        return PluginConfiguration(configuration_key, {})
