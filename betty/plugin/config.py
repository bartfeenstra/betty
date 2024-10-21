"""
Provide plugin configuration.
"""

from __future__ import annotations

from typing import TypeVar, Generic, cast, Sequence, Any, TYPE_CHECKING

from typing_extensions import override

from betty.assertion import (
    RequiredField,
    assert_record,
    OptionalField,
    assert_setattr,
    Field,
    assert_field,
)
from betty.config import Configuration, DefaultConfigurable
from betty.config.collections.mapping import ConfigurationMapping
from betty.locale.localizable.config import (
    OptionalStaticTranslationsLocalizableConfigurationAttr,
    RequiredStaticTranslationsLocalizableConfigurationAttr,
)
from betty.machine_name import assert_machine_name, MachineName
from betty.plugin import Plugin, PluginRepository
from betty.plugin.assertion import assert_plugin

if TYPE_CHECKING:
    from betty.locale.localizable import ShorthandStaticTranslations
    from betty.serde.dump import Dump, DumpMapping

_PluginT = TypeVar("_PluginT", bound=Plugin)
_PluginCoT = TypeVar("_PluginCoT", bound=Plugin, covariant=True)


class PluginConfiguration(Configuration):
    """
    Configure a single plugin.
    """

    label = RequiredStaticTranslationsLocalizableConfigurationAttr("label")
    description = OptionalStaticTranslationsLocalizableConfigurationAttr("description")

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
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("id", assert_machine_name() | assert_setattr(self, "_id")),
            RequiredField("label", self.label.load),
            OptionalField("description", self.description.load),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "id": self.id,
            "label": self.label.dump(),
            "description": self.description.dump(),
        }


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
    def _get_key(self, configuration: _PluginConfigurationT) -> str:
        return configuration.id

    @override
    def _load_key(self, item_dump: DumpMapping[Dump], key_dump: str) -> None:
        item_dump["id"] = key_dump

    @override
    def _dump_key(self, item_dump: DumpMapping[Dump]) -> str:
        return cast(str, item_dump.pop("id"))


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


class PluginInstanceConfiguration(Configuration, Generic[_PluginT]):
    """
    Configure a single plugin instance.

    Plugins that extend :py:class:`betty.config.DefaultConfigurable` may receive their configuration from
    :py:attr:`betty.plugin.config.PluginInstanceConfiguration.plugin_configuration` / the `"configuration"` dump key.
    """

    def __init__(
        self,
        plugin: type[_PluginT],
        *,
        plugin_repository: PluginRepository[_PluginT],
        plugin_configuration: Configuration | None = None,
    ):
        if plugin_configuration and not issubclass(plugin, DefaultConfigurable):
            raise ValueError(
                f"{plugin} is not configurable (it must extend {DefaultConfigurable}), but configuration was given."
            )
        if (
            issubclass(plugin, DefaultConfigurable)  # type: ignore[redundant-expr]
            and not plugin_configuration  # type: ignore[unreachable]
        ):
            plugin_configuration = plugin.new_default_configuration()  # type: ignore[unreachable]
        super().__init__()
        self._plugin = plugin
        self._plugin_configuration = plugin_configuration
        self._plugin_repository = plugin_repository

    @property
    def plugin(self) -> type[_PluginT]:
        """
        The plugin.
        """
        return self._plugin

    @property
    def plugin_configuration(self) -> Configuration | None:
        """
        Get the plugin's own configuration.
        """
        return self._plugin_configuration

    @override
    def load(self, dump: Dump) -> None:
        id_field = RequiredField(
            "id",
            assert_plugin(self._plugin_repository) | assert_setattr(self, "_plugin"),
        )
        plugin = assert_field(id_field)(dump)
        fields = [id_field, *self._fields()]
        if issubclass(plugin, DefaultConfigurable):
            configuration = plugin.new_default_configuration()
            self._plugin_configuration = configuration
            fields.append(OptionalField("configuration", configuration.load))
        assert_record(*fields)(dump)

    def _fields(self) -> Sequence[Field[Any, Any]]:
        return []

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump: DumpMapping[Dump] = {"id": self.plugin.plugin_id()}
        if issubclass(self.plugin, DefaultConfigurable):  # type: ignore[redundant-expr]
            dump["configuration"] = self.plugin_configuration.dump()  # type: ignore[unreachable]
        return dump
