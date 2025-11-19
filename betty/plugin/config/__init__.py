"""
Provide plugin configuration.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_fields,
    assert_mapping,
    assert_or,
    assert_record,
    assert_setattr,
)
from betty.config import Configuration, DefaultConfigurable
from betty.config.collections import ConfigurationKey
from betty.config.collections.mapping import ConfigurationMapping
from betty.config.collections.sequence import ConfigurationSequence
from betty.exception import HumanFacingException
from betty.locale.localizable import _
from betty.locale.localizable.assertion import assert_static_translations
from betty.locale.localizable.config import (
    OptionalStaticTranslationsConfigurationAttr,
    RequiredStaticTranslationsConfigurationAttr,
)
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    PluginDefinition,
    PluginIdentifier,
    PluginRepository,
    resolve_id,
)
from betty.typing import Void, Voidable

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.factory import Factory
    from betty.locale.localizable import ShorthandStaticTranslations
    from betty.serde.dump import Dump, DumpMapping

_PluginT = TypeVar("_PluginT")
_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)
_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)
_ClassedPluginDefinitionT = TypeVar(
    "_ClassedPluginDefinitionT", bound=ClassedPluginDefinition[Any]
)


class PluginIdentifierKeyConfigurationMapping(
    ConfigurationMapping[MachineName, _ConfigurationT],
    Generic[_PluginDefinitionT, _ConfigurationT],
):
    """
    A mapping of configuration, keyed by a plugin identifier.
    """

    @override
    def __getitem__(
        self, configuration_key: PluginIdentifier[_PluginDefinitionT]
    ) -> _ConfigurationT:
        return super().__getitem__(resolve_id(configuration_key))

    @override
    def __contains__(
        self, configuration_key: PluginIdentifier[_PluginDefinitionT]
    ) -> bool:
        return super().__contains__(resolve_id(configuration_key))


class PluginDefinitionConfiguration(Configuration):
    """
    Configure a :py:class:`betty.plugin.PluginDefinition`.
    """

    def __init__(
        self,
        *,
        id: MachineName,  # noqa A002
    ):
        super().__init__()
        self._id = assert_machine_name()(id)

    @property
    def id(self) -> str:
        """
        The configured plugin ID.
        """
        return self._id

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        assert_record(
            RequiredField("id", assert_machine_name() | assert_setattr(self, "_id")),
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "id": self.id,
        }


class HumanFacingPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.plugin.HumanFacingPluginDefinition`.
    """

    label = RequiredStaticTranslationsConfigurationAttr("label")
    description = OptionalStaticTranslationsConfigurationAttr("description")

    def __init__(
        self,
        *,
        label: ShorthandStaticTranslations,
        description: ShorthandStaticTranslations | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label = label
        if description is not None:
            self.description = description

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()

        mapping = assert_mapping()(dump)
        assert_fields(
            RequiredField(
                "label",
                assert_static_translations() | assert_setattr(self, "label"),
            ),
            OptionalField(
                "description",
                assert_static_translations() | assert_setattr(self, "description"),
            ),
        )(mapping)
        mapping.pop("label", None)
        mapping.pop("description", None)
        super().load(mapping)

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump = super().dump()
        dump["label"] = self.label.dump()
        dump["description"] = self.description.dump()
        return dump


_PluginConfigurationT = TypeVar(
    "_PluginConfigurationT", bound=PluginDefinitionConfiguration
)


class PluginDefinitionConfigurationMapping(
    ConfigurationMapping[MachineName, _PluginConfigurationT],
    Generic[_PluginDefinitionT, _PluginConfigurationT],
):
    """
    Configure a collection of plugins.
    """

    def new_plugins(self) -> Sequence[_PluginDefinitionT]:
        """
        Create the plugins for this configuration.

        You SHOULD NOT cache the value anywhere, as it *will* change
        when this configuration changes.
        """
        return tuple(
            self._new_plugin(plugin_configuration)
            for plugin_configuration in self.values()
        )

    @abstractmethod
    def _new_plugin(self, configuration: _PluginConfigurationT) -> _PluginDefinitionT:
        """
        The plugin (class) for the given configuration.
        """

    @override
    def _get_key(self, configuration: _PluginConfigurationT) -> str:
        return configuration.id

    @override
    def _load_key(self, item_dump: Dump, key_dump: str) -> Dump:
        assert isinstance(item_dump, Mapping)
        item_dump["id"] = key_dump
        return item_dump

    @override
    def _dump_key(self, item_dump: Dump) -> tuple[Dump, str]:
        assert isinstance(item_dump, Mapping)
        return item_dump, cast(str, item_dump.pop("id"))


class PluginInstanceConfiguration(
    Generic[_ClassedPluginDefinitionT, _PluginT], Configuration
):
    """
    Configure a single plugin instance.

    Plugins that extend :py:class:`betty.config.DefaultConfigurable` may receive their configuration from
    :py:attr:`betty.plugin.config.PluginInstanceConfiguration.configuration` / the `"configuration"` dump key.
    """

    def __init__(
        self,
        plugin: PluginIdentifier[_ClassedPluginDefinitionT, _PluginT & ClassedPlugin],
        *,
        configuration: Voidable[Configuration | Dump] = Void(),  # noqa B008
    ):
        super().__init__()
        self._id = assert_machine_name()(resolve_id(plugin))
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

    async def new_plugin_instance(
        self,
        repository: PluginRepository[_ClassedPluginDefinitionT],
        *,
        factory: Factory,
    ) -> _PluginT:
        """
        Create a new plugin instance.
        """
        plugin_definition = cast(ClassedPluginDefinition[_PluginT], repository[self.id])
        plugin = await factory(plugin_definition.cls)
        if not isinstance(self.configuration, Void):
            if not isinstance(plugin, DefaultConfigurable):
                raise HumanFacingException(
                    _(
                        'Plugin "{plugin_id}" is not configurable, but configuration was given.'
                    ).format(plugin_id=plugin_definition.id)
                )
            plugin.configuration.load(self.configuration)
        return plugin

    @override
    def load(self, dump: Dump) -> None:
        self.assert_mutable()
        id_assertion = assert_machine_name() | assert_setattr(self, "_id")
        assert_or(
            id_assertion,
            assert_record(
                RequiredField("id", id_assertion),
                OptionalField("configuration", assert_setattr(self, "_configuration")),
            ),
        )(dump)

    @override
    def dump(self) -> Dump:
        configuration = self.configuration
        if isinstance(configuration, Void):
            return self.id
        return {
            "id": self.id,
            "configuration": configuration,
        }


class PluginInstanceConfigurationMapping(
    PluginIdentifierKeyConfigurationMapping[
        _ClassedPluginDefinitionT,
        PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT],
    ],
    Generic[_ClassedPluginDefinitionT, _PluginT],
):
    """
    Configure plugin instances, keyed by their plugin IDs.
    """

    def __init__(
        self,
        configurations: Iterable[
            PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]
        ]
        | None = None,
        /,
    ):
        super().__init__(configurations)

    @override
    def _load_item(
        self, dump: Dump
    ) -> PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]:
        configuration = PluginInstanceConfiguration[
            _ClassedPluginDefinitionT, _PluginT
        ]("-")
        configuration.load(dump)
        return configuration

    @override
    def _get_key(
        self,
        configuration: PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT],
    ) -> MachineName:
        return configuration.id

    @override
    def _load_key(self, item_dump: Dump, key_dump: str) -> Dump:
        if not item_dump:
            return key_dump
        assert isinstance(item_dump, Mapping)
        item_dump["id"] = key_dump
        return item_dump

    @override
    def _dump_key(self, item_dump: Dump) -> tuple[Dump, str]:
        if isinstance(item_dump, str):
            return {}, item_dump
        assert isinstance(item_dump, Mapping)
        return item_dump, cast(str, item_dump.pop("id"))


class PluginInstanceConfigurationSequence(
    ConfigurationSequence[
        PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]
    ],
    Generic[_ClassedPluginDefinitionT, _PluginT],
):
    """
    Configure plugin instances.
    """

    def __init__(
        self,
        configurations: Iterable[
            PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]
        ]
        | None = None,
        /,
    ):
        super().__init__(configurations)

    @override
    def _load_item(
        self, dump: Dump
    ) -> PluginInstanceConfiguration[_ClassedPluginDefinitionT, _PluginT]:
        configuration = PluginInstanceConfiguration[
            _ClassedPluginDefinitionT, _PluginT
        ]("-")
        configuration.load(dump)
        return configuration
