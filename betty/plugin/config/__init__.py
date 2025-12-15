"""
Provide plugin configuration.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Generic, Self, cast

from typing_extensions import TypeVar, override

from betty.assertion import (
    Field,
    OptionalField,
    RequiredField,
    assert_or,
    assert_record,
)
from betty.config import Configuration
from betty.config.collections import ConfigurationKey
from betty.config.collections.mapping import ConfigurationMapping
from betty.config.collections.sequence import ConfigurationSequence
from betty.locale.localizable.assertion import (
    assert_load_countable_localizable,
    assert_load_localizable,
)
from betty.locale.localizable.attr import (
    OptionalLocalizableAttr,
    RequiredCountableLocalizableAttr,
    RequiredLocalizableAttr,
)
from betty.locale.localizable.config import dump_countable_localizable, dump_localizable
from betty.locale.localizable.ensure import (
    ensure_countable_localizable,
    ensure_localizable,
)
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.typing import Void

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.locale.localizable import CountableLocalizableLike, LocalizableLike
    from betty.serde.dump import Dump, DumpMapping

_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration, default=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class PluginIdentifierKeyConfigurationMapping(
    ConfigurationMapping[
        MachineName, ResolvableId[_PluginDefinitionT], _ConfigurationT
    ],
    Generic[_PluginDefinitionT, _ConfigurationT],
):
    """
    A mapping of configuration, keyed by a plugin identifier.
    """

    @override
    def _resolve_key(
        self, configuration_key: ResolvableId[_PluginDefinitionT], /
    ) -> MachineName:
        return resolve_id(configuration_key)


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
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls(**assert_record(*cls.fields())(dump))

    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        """
        The configuration fields.
        """
        return [
            RequiredField("id", assert_machine_name()),
        ]

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
    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        return [
            *super().fields(),
            RequiredField("label", assert_load_localizable),
            OptionalField("description", assert_load_localizable),
        ]

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump = super().dump()
        dump["label"] = dump_localizable(self.label)
        if self.description is not None:
            dump["description"] = dump_localizable(self.description)
        return dump


class CountableHumanFacingPluginDefinitionConfiguration(
    HumanFacingPluginDefinitionConfiguration
):
    """
    Configure a :py:class:`betty.plugin.human_facing.CountableHumanFacingPluginDefinition`.
    """

    label_plural = RequiredLocalizableAttr("label_plural")
    label_countable = RequiredCountableLocalizableAttr("label_countable")

    def __init__(
        self,
        *,
        label_plural: LocalizableLike,
        label_countable: CountableLocalizableLike,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label_plural = ensure_localizable(label_plural)
        self.label_countable = ensure_countable_localizable(label_countable)

    @override
    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        return [
            *super().fields(),
            RequiredField("label_plural", assert_load_localizable),
            RequiredField("label_countable", assert_load_countable_localizable),
        ]

    @override
    def dump(self) -> DumpMapping[Dump]:
        dump = super().dump()
        dump["label_plural"] = dump_localizable(self.label_plural)
        dump["label_countable"] = dump_countable_localizable(self.label_countable)
        return dump


_PluginDefinitionConfigurationT = TypeVar(
    "_PluginDefinitionConfigurationT",
    bound=PluginDefinitionConfiguration,
    default=PluginDefinitionConfiguration,
)


class PluginDefinitionConfigurationMapping(
    ConfigurationMapping[
        MachineName, ResolvableId[_PluginDefinitionT], _PluginDefinitionConfigurationT
    ],
    Generic[_PluginDefinitionT, _PluginDefinitionConfigurationT],
):
    """
    Configure a collection of plugins.
    """

    @override
    def _resolve_key(
        self, configuration_key: ResolvableId[_PluginDefinitionT], /
    ) -> MachineName:
        return resolve_id(configuration_key)

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
        self, configuration: _PluginDefinitionConfigurationT, /
    ) -> _PluginDefinitionT:
        """
        The plugin (class) for the given configuration.
        """

    @override
    def _get_key(self, configuration: _PluginDefinitionConfigurationT, /) -> str:
        return configuration.id

    @override
    @classmethod
    def _load_key(cls, item_dump: Dump, key_dump: str, /) -> Dump:
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
        id: ResolvableId[_PluginDefinitionT],  # noqa A002
        configuration: Configuration | Dump | Void = Void(),  # noqa B008
        /,
    ):
        super().__init__()
        self._id = assert_machine_name()(resolve_id(id))
        self._configuration = configuration

    @property
    def id(self) -> MachineName:
        """
        The plugin ID.
        """
        return self._id

    @property
    def configuration(self) -> Configuration | Dump | Void:
        """
        Get the plugin's own configuration.
        """
        return self._configuration

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        id_assertion = assert_machine_name()
        record = assert_or(
            id_assertion | (lambda plugin_id: {"id": plugin_id}),
            assert_record(
                RequiredField("id", id_assertion),
                OptionalField("configuration"),
            ),
        )(dump)
        return cls(record["id"], record.get("configuration", Void()))

    @override
    def dump(self) -> Dump:
        configuration = self.configuration
        if isinstance(configuration, Void):
            return self._id
        return {
            "id": self._id,
            "configuration": configuration.dump()
            if isinstance(configuration, Configuration)
            else configuration,
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
    @classmethod
    def _load_item(
        cls, dump: Dump
    ) -> PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]:
        return PluginInstanceConfiguration.load(dump)

    @override
    def _get_key(
        self,
        configuration: PluginInstanceConfiguration[_PluginDefinitionT, _PluginT],
        /,
    ) -> MachineName:
        return configuration.id

    @override
    @classmethod
    def _load_key(cls, item_dump: Dump, key_dump: str, /) -> Dump:
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
    @classmethod
    def _load_item(
        cls, dump: Dump
    ) -> PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]:
        return PluginInstanceConfiguration.load(dump)
