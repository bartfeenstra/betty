"""
Provide plugin configuration.
"""

from __future__ import annotations

from typing import TypeVar, Generic, cast, Sequence, TYPE_CHECKING

from typing_extensions import override

from betty.assertion import (
    RequiredField,
    assert_record,
    OptionalField,
    assert_setattr,
    assert_field,
)
from betty.assertion.error import AssertionFailed
from betty.config import Configuration, DefaultConfigurable
from betty.config.collections.mapping import ConfigurationMapping
from betty.locale.localizable import _
from betty.locale.localizable.config import (
    OptionalStaticTranslationsLocalizableConfigurationAttr,
    RequiredStaticTranslationsLocalizableConfigurationAttr,
)
from betty.machine_name import assert_machine_name, MachineName
from betty.plugin import Plugin, PluginRepository
from betty.typing import Void, Voidable

if TYPE_CHECKING:
    from collections.abc import Iterable
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
    def new_plugins(self) -> Sequence[type[_PluginCoT]]:
        """
        The plugins for this configuration.

        You SHOULD NOT cache the value anywhere, as it *will* change
        when this configuration changes.
        """
        return tuple(
            self._new_plugin(plugin_configuration)
            for plugin_configuration in self.values()
        )

    def _new_plugin(self, configuration: _PluginConfigurationT) -> type[_PluginCoT]:
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


class PluginInstanceConfiguration(Configuration):
    """
    Configure a single plugin instance.

    Plugins that extend :py:class:`betty.config.DefaultConfigurable` may receive their configuration from
    :py:attr:`betty.plugin.config.PluginInstanceConfiguration.configuration` / the `"configuration"` dump key.
    """

    def __init__(
        self,
        plugin_id: type[Plugin] | MachineName,
        *,
        configuration: Voidable[Configuration | Dump] = Void,
    ):
        super().__init__()
        self._id = (
            assert_machine_name()(plugin_id)
            if isinstance(plugin_id, str)
            else plugin_id.plugin_id()
        )
        self._configuration = (
            configuration.dump()
            if isinstance(configuration, Configuration)
            else configuration
        )

    @property
    def id(self) -> MachineName:
        """
        The plugin ID.
        """
        return self._id

    @property
    def configuration(self) -> Voidable[Dump]:
        """
        Get the plugin's own configuration.
        """
        return self._configuration

    # @todo Allow assertion contexts to be passed on?
    # @todo Evaluate this based on calling code.
    async def new_plugin_instance(
        self, repository: PluginRepository[_PluginT]
    ) -> _PluginT:
        """
        Create a new plugin instance.
        """
        plugin = await repository.new_target(self.id)
        if self.configuration is not Void:
            if not isinstance(plugin, DefaultConfigurable):  # type: ignore[redundant-expr]
                raise AssertionFailed(
                    _(
                        "Plugin {plugin_label} ({plugin_id}) is not configurable, but configuration was given."
                    ).format(
                        plugin_id=plugin.plugin_id(), plugin_label=plugin.plugin_label()
                    )
                )
            plugin.configuration.load(self.configuration)  # type: ignore[unreachable]
        return plugin

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("id", assert_machine_name() | assert_setattr(self, "_id")),
            OptionalField("configuration", assert_setattr(self, "_configuration")),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump: DumpMapping[Dump] = {"id": self.id}
        configuration = self.configuration
        if configuration is not Void:
            dump["configuration"] = configuration  # type: ignore[assignment]
        return dump


class PluginInstanceConfigurationMapping(
    ConfigurationMapping[MachineName, PluginInstanceConfiguration]
):
    """
    Configure plugin instances, keyed by their plugin IDs.
    """

    def __init__(
        self,
        configurations: Iterable[PluginInstanceConfiguration] | None = None,
    ):
        super().__init__(configurations)

    @override
    def load_item(self, dump: Dump) -> PluginInstanceConfiguration:
        plugin_id = assert_field(RequiredField("id", assert_machine_name()))(dump)
        configuration = PluginInstanceConfiguration(plugin_id)
        configuration.load(dump)
        return configuration

    @override
    def _get_key(self, configuration: PluginInstanceConfiguration) -> MachineName:
        return configuration.id

    @override
    def _load_key(self, item_dump: DumpMapping[Dump], key_dump: str) -> None:
        item_dump["id"] = key_dump

    @override
    def _dump_key(self, item_dump: DumpMapping[Dump]) -> str:
        return cast(str, item_dump.pop("id"))
