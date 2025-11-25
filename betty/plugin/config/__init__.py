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
from betty.config import Configurable, Configuration
from betty.config.collections import ConfigurationKey
from betty.config.collections.mapping import ConfigurationMapping
from betty.config.collections.sequence import ConfigurationSequence
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.exception import HumanFacingException
from betty.importlib import fully_qualified_name
from betty.locale.localizable import (
    LocalizableLike,
    OptionalLocalizableAttr,
    RequiredLocalizableAttr,
    _,
    ensure_localizable,
)
from betty.locale.localizable.assertion import assert_load_localizable
from betty.locale.localizable.config import dump_localizable
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.typing import Void, Voidable

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.plugin.repository import PluginRepository
    from betty.serde.dump import Dump, DumpMapping
    from betty.service.level.factory import AnyFactory

_PluginT = TypeVar("_PluginT", bound=Plugin)
_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)
_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


class PluginIdentifierKeyConfigurationMapping(
    ConfigurationMapping[MachineName, _ConfigurationT],
    Generic[_PluginDefinitionT, _ConfigurationT],
):
    """
    A mapping of configuration, keyed by a plugin identifier.
    """

    @override
    def __getitem__(
        self, configuration_key: ResolvableId[_PluginDefinitionT]
    ) -> _ConfigurationT:
        return super().__getitem__(resolve_id(configuration_key))

    @override
    def __contains__(self, configuration_key: ResolvableId[_PluginDefinitionT]) -> bool:
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
    def load(self, dump: Dump, /) -> None:
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
    Configure a :py:class:`betty.plugin.human_facing.HumanFacingPluginDefinition`.
    """

    label = RequiredLocalizableAttr("label")
    description = OptionalLocalizableAttr("description")

    def __init__(
        self,
        *,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label = ensure_localizable(label)
        if description is not None:
            self.description = ensure_localizable(description)

    @override
    def load(self, dump: Dump, /) -> None:
        self.assert_mutable()

        mapping = assert_mapping()(dump)
        assert_fields(
            RequiredField(
                "label", assert_load_localizable | assert_setattr(self, "label")
            ),
            OptionalField(
                "description",
                assert_load_localizable | assert_setattr(self, "description"),
            ),
        )(mapping)
        mapping.pop("label", None)
        mapping.pop("description", None)
        super().load(mapping)

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump = super().dump()
        dump["label"] = dump_localizable(self.label)
        if self.description is not None:
            dump["description"] = dump_localizable(self.description)
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
    def _new_plugin(
        self, configuration: _PluginConfigurationT, /
    ) -> _PluginDefinitionT:
        """
        The plugin (class) for the given configuration.
        """

    @override
    def _get_key(self, configuration: _PluginConfigurationT, /) -> str:
        return configuration.id

    @override
    def _load_key(self, item_dump: Dump, key_dump: str, /) -> Dump:
        assert isinstance(item_dump, Mapping)
        item_dump["id"] = key_dump
        return item_dump

    @override
    def _dump_key(self, item_dump: Dump, /) -> tuple[Dump, str]:
        assert isinstance(item_dump, Mapping)
        return item_dump, cast(str, item_dump.pop("id"))


class PluginInstanceConfiguration(Generic[_PluginDefinitionT, _PluginT], Configuration):
    """
    Configure a single plugin instance.
    """

    def __init__(
        self,
        plugin: ResolvableId[_PluginDefinitionT, _PluginT & Plugin],
        configuration: Voidable[Configuration | Dump] = Void(),  # noqa B008
        /,
    ):
        super().__init__()
        self._id = assert_machine_name()(resolve_id(plugin))
        self._configuration = configuration

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
        return (
            self._configuration.dump()
            if isinstance(self._configuration, Configuration)
            else self._configuration
        )

    async def new_plugin_instance(
        self,
        repository: PluginRepository[_PluginDefinitionT],
        *,
        factory: AnyFactory,
    ) -> _PluginT:
        """
        Create a new plugin instance.
        """
        plugin_definition = repository[self._id]
        if not isinstance(self._configuration, Void):
            if not issubclass(plugin_definition.cls, Configurable):
                raise HumanFacingException(
                    _(
                        'Plugin "{plugin_id}" is not configurable, but configuration was given.'
                    ).format(plugin_id=plugin_definition.id)
                )
            if isinstance(self._configuration, Configuration):
                if not issubclass(
                    plugin_definition.cls, ConfigurationDependentSelfFactory
                ):
                    raise HumanFacingException(
                        f"Cannot instantiate {fully_qualified_name(plugin_definition.cls)} with configuration because it does not subclass {fully_qualified_name(ConfigurationDependentSelfFactory)}."
                    )
                return await factory(
                    plugin_definition.cls.new_for_configuration(self._configuration)  # type: ignore[arg-type]
                )
            plugin = await factory(
                cast(type[Configurable[Configuration]], plugin_definition.cls)
            )
            plugin.configuration.load(self._configuration)
            return plugin  # type: ignore[return-value]
        return await factory(
            plugin_definition.cls,  # type: ignore[arg-type]
        )

    @override
    def load(self, dump: Dump, /) -> None:
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
            return self._id
        return {
            "id": self._id,
            "configuration": configuration,
        }


class PluginInstanceConfigurationMapping(
    PluginIdentifierKeyConfigurationMapping[
        _PluginDefinitionT,
        PluginInstanceConfiguration[_PluginDefinitionT, _PluginT],
    ],
    Generic[_PluginDefinitionT, _PluginT],
):
    """
    Configure plugin instances, keyed by their plugin IDs.
    """

    def __init__(
        self,
        configurations: Iterable[
            PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]
        ]
        | None = None,
        /,
    ):
        super().__init__(configurations)

    @override
    def _load_item(
        self, dump: Dump
    ) -> PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]:
        configuration = PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]("-")
        configuration.load(dump)
        return configuration

    @override
    def _get_key(
        self,
        configuration: PluginInstanceConfiguration[_PluginDefinitionT, _PluginT],
        /,
    ) -> MachineName:
        return configuration.id

    @override
    def _load_key(self, item_dump: Dump, key_dump: str, /) -> Dump:
        if not item_dump:
            return key_dump
        assert isinstance(item_dump, Mapping)
        item_dump["id"] = key_dump
        return item_dump

    @override
    def _dump_key(self, item_dump: Dump, /) -> tuple[Dump, str]:
        if isinstance(item_dump, str):
            return {}, item_dump
        assert isinstance(item_dump, Mapping)
        return item_dump, cast(str, item_dump.pop("id"))


class PluginInstanceConfigurationSequence(
    ConfigurationSequence[PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]],
    Generic[_PluginDefinitionT, _PluginT],
):
    """
    Configure plugin instances.
    """

    def __init__(
        self,
        configurations: Iterable[
            PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]
        ]
        | None = None,
        /,
    ):
        super().__init__(configurations)

    @override
    def _load_item(
        self, dump: Dump
    ) -> PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]:
        configuration = PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]("-")
        configuration.load(dump)
        return configuration
