"""
Provide plugin configuration.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection, Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Generic, Self, TypeAlias, cast, final

from typing_extensions import TypeVar, override

from betty.assertion import (
    Field,
    OptionalField,
    RequiredField,
    assert_or,
    assert_record,
)
from betty.config import Configuration, Sample, get_full_sample
from betty.config.collections import ConfigurationCollection, ConfigurationKey
from betty.config.collections.mapping import ConfigurationMapping
from betty.config.collections.sequence import ConfigurationSequence
from betty.config.color import ColorConfiguration
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.assertion import (
    assert_load_countable_localizable,
    assert_load_localizable,
)
from betty.locale.localizable.attr import (
    OptionalLocalizableAttr,
    RequiredCountableLocalizableAttr,
    RequiredLocalizableAttr,
)
from betty.locale.localizable.ensure import (
    ensure_countable_localizable,
    ensure_localizable,
)
from betty.locale.localizable.serde import dump_countable_localizable, dump_localizable
from betty.locale.localizable.static import CountableStaticTranslations
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.typing import Void

if TYPE_CHECKING:
    from betty.locale.localizable import CountableLocalizableLike, LocalizableLike
    from betty.serde import SerializedData, SerializedMapping

_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration, default=Configuration)
_ConfigurationKeyT = TypeVar("_ConfigurationKeyT", bound=ConfigurationKey)
_ResolvableConfigurationKeyT = TypeVar("_ResolvableConfigurationKeyT")
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

    .. configuration:: betty.plugin.config:PluginDefinitionConfiguration
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
    def load(cls, serialized: SerializedData, /) -> Self:
        return cls(**assert_record(*cls.fields())(serialized))

    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        """
        The configuration fields.
        """
        return [
            RequiredField("id", assert_machine_name()),
        ]

    @override
    def dump(self) -> SerializedMapping[SerializedData]:
        return {
            "id": self.id,
        }

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(id="my-custom-plugin"), label="Default")


class HumanFacingPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.plugin.human_facing.HumanFacingPluginDefinition`.

    .. configuration:: betty.plugin.config:HumanFacingPluginDefinitionConfiguration
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
    def dump(self) -> SerializedMapping[SerializedData]:
        serialized = super().dump()
        serialized["label"] = dump_localizable(self.label)
        if self.description is not None:
            serialized["description"] = dump_localizable(self.description)
        return serialized

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        eq = super().__eq__(other)
        if eq is not True:
            return eq
        return (self.label, self.description) == (other.label, other.description)

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
            cls(id="my-custom-plugin", label="My Custom Plugin"),
            label="Minimal",
            minimal=True,
        )
        yield Sample(
            cls(
                id="my-custom-plugin",
                label="My Custom Plugin",
                description="My Custom Plugin is the best plugin for your needs.",
            ),
            label="Full",
            full=True,
        )


class CountableHumanFacingPluginDefinitionConfiguration(
    HumanFacingPluginDefinitionConfiguration
):
    """
    Configure a :py:class:`betty.plugin.human_facing.CountableHumanFacingPluginDefinition`.

    .. configuration:: betty.plugin.config:CountableHumanFacingPluginDefinitionConfiguration
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
    def dump(self) -> SerializedMapping[SerializedData]:
        serialized = super().dump()
        serialized["label_plural"] = dump_localizable(self.label_plural)
        serialized["label_countable"] = dump_countable_localizable(self.label_countable)
        return serialized

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        eq = super().__eq__(other)
        if eq is not True:
            return eq
        return (self.label_plural, self.label_countable) == (
            other.label_plural,
            other.label_countable,
        )

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
            cls(
                id="my-custom-plugin",
                label="My Custom Plugin",
                label_plural="My Custom Plugins",
                label_countable=CountableStaticTranslations(
                    {
                        DEFAULT_LOCALE: {
                            "one": "{count} My Custom Plugin",
                            "other": "{count} My Custom Plugins",
                        }
                    }
                ),
            ),
            label="Minimal",
            minimal=True,
        )
        yield Sample(
            cls(
                id="my-custom-plugin",
                label="My Custom Plugin",
                label_plural="My Custom Plugins",
                label_countable=CountableStaticTranslations(
                    {
                        DEFAULT_LOCALE: {
                            "one": "{count} My Custom Plugin",
                            "other": "{count} My Custom Plugins",
                        }
                    }
                ),
                description="My Custom Plugin is the best plugin for your needs.",
            ),
            label="Full",
            full=True,
        )


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
    def _load_key(
        cls, serialized_item: SerializedData, serialized_key: str, /
    ) -> SerializedData:
        assert isinstance(serialized_item, Mapping)
        serialized_item["id"] = serialized_key
        return serialized_item

    @override
    def _dump_key(
        self, serialized_item: SerializedData, /
    ) -> tuple[SerializedData, str]:
        assert isinstance(serialized_item, Mapping)
        return serialized_item, cast(str, serialized_item.pop("id"))


class PluginInstanceConfiguration(Generic[_PluginDefinitionT, _PluginT], Configuration):
    """
    Configure a single plugin instance.

    .. configuration:: betty.plugin.config:PluginInstanceConfiguration
    """

    def __init__(
        self,
        id: ResolvableId[_PluginDefinitionT],  # noqa A002
        configuration: Configuration | SerializedData | Void = Void(),  # noqa B008
        /,
    ):
        super().__init__()
        self._id = assert_machine_name()(resolve_id(id))
        self._configuration = configuration

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.id, self.configuration) == (other.id, other.configuration)

    @property
    def id(self) -> MachineName:
        """
        The plugin ID.
        """
        return self._id

    @property
    def configuration(self) -> Configuration | SerializedData | Void:
        """
        Get the plugin's own configuration.
        """
        return self._configuration

    @override
    @classmethod
    def load(cls, serialized: SerializedData, /) -> Self:
        id_assertion = assert_machine_name()
        record = assert_or(
            id_assertion | (lambda plugin_id: {"id": plugin_id}),
            assert_record(
                RequiredField("id", id_assertion),
                OptionalField("configuration"),
            ),
        )(serialized)
        return cls(record["id"], record.get("configuration", Void()))

    @override
    def dump(self) -> SerializedData:
        configuration = self.configuration
        if isinstance(configuration, Void):
            return self._id
        return {
            "id": self._id,
            "configuration": configuration.dump()
            if isinstance(configuration, Configuration)
            else configuration,
        }

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        from betty.project.extension.raspberry_mint import RaspberryMint
        from betty.project.extension.raspberry_mint.config import (
            RaspberryMintConfiguration,
        )

        yield Sample(
            cls(
                RaspberryMint,  # type: ignore[arg-type]
            ),
            label="Minimal",
            minimal=True,
        )
        yield Sample(
            cls(
                RaspberryMint,  # type: ignore[arg-type]
                RaspberryMintConfiguration(primary_color=ColorConfiguration("#ff0000")),
            ),
            label="Full",
            full=True,
        )


ShorthandPluginInstanceConfigurationSequence: TypeAlias = (
    PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]
    | Iterable[PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]]
)


class _PluginInstanceConfigurationCollection(
    ConfigurationCollection[
        _ConfigurationKeyT,
        _ResolvableConfigurationKeyT,
        PluginInstanceConfiguration[_PluginDefinitionT, _PluginT],
    ]
):
    def __init__(
        self,
        configurations: ShorthandPluginInstanceConfigurationSequence[
            _PluginDefinitionT, _PluginT
        ]
        | None = None,
        /,
    ):
        if isinstance(configurations, PluginInstanceConfiguration):
            configurations = [configurations]
        super().__init__(configurations)

    @override
    @classmethod
    def _item_cls(
        cls,
    ) -> type[PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]]:
        return PluginInstanceConfiguration


class PluginInstanceConfigurationMapping(
    _PluginInstanceConfigurationCollection[
        MachineName, ResolvableId[_PluginDefinitionT], _PluginDefinitionT, _PluginT
    ],
    PluginIdentifierKeyConfigurationMapping[
        _PluginDefinitionT,
        PluginInstanceConfiguration[_PluginDefinitionT, _PluginT],
    ],
):
    """
    Configure plugin instances, keyed by their plugin IDs.

    .. configuration:: betty.plugin.config:PluginInstanceConfigurationMapping
    """

    def __init__(
        self,
        configurations: ShorthandPluginInstanceConfigurationSequence[
            _PluginDefinitionT, _PluginT
        ]
        | None = None,
        /,
    ):
        super().__init__(configurations)

    @override
    def _get_key(
        self,
        configuration: PluginInstanceConfiguration[_PluginDefinitionT, _PluginT],
        /,
    ) -> MachineName:
        return configuration.id

    @override
    @classmethod
    def _load_key(
        cls, serialized_item: SerializedData, serialized_key: str, /
    ) -> SerializedData:
        if not serialized_item:
            return serialized_key
        assert isinstance(serialized_item, Mapping)
        serialized_item["id"] = serialized_key
        return serialized_item

    @override
    def _dump_key(
        self, serialized_item: SerializedData, /
    ) -> tuple[SerializedData, str]:
        if isinstance(serialized_item, str):
            return {}, serialized_item
        assert isinstance(serialized_item, Mapping)
        return serialized_item, cast(str, serialized_item.pop("id"))

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(PluginInstanceConfiguration).configuration]),
            label="Full",
            full=True,
        )


@final
class PluginInstanceConfigurationSequence(
    _PluginInstanceConfigurationCollection[int, int, _PluginDefinitionT, _PluginT],
    ConfigurationSequence[PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]],
):
    """
    A sequence of plugin instance configurations.

    .. configuration:: betty.plugin.config:PluginInstanceConfigurationSequence
    """

    @override
    @classmethod
    def samples(
        cls,
    ) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Minimal", minimal=True)
        yield Sample(
            cls([get_full_sample(PluginInstanceConfiguration).configuration]),
            label="Full",
            full=True,
        )


ShorthandPluginInstanceConfigurationSequenceSequence: TypeAlias = (
    Iterable[ShorthandPluginInstanceConfigurationSequence[_PluginDefinitionT, _PluginT]]
    | PluginInstanceConfiguration[_PluginDefinitionT, _PluginT]
)


class PluginInstanceConfigurationSequenceSequence(
    ConfigurationSequence[
        PluginInstanceConfigurationSequence[_PluginDefinitionT, _PluginT]
    ],
    Generic[_PluginDefinitionT, _PluginT],
):
    """
    A sequence of sequences of plugin instance configurations.

    .. configuration:: betty.plugin.config:PluginInstanceConfigurationSequenceSequence
    """

    def __init__(
        self,
        configurations: ShorthandPluginInstanceConfigurationSequenceSequence[
            _PluginDefinitionT, _PluginT
        ],
        /,
    ):
        if isinstance(configurations, PluginInstanceConfiguration):
            configurations = [configurations]
        super().__init__(
            configuration
            if isinstance(configuration, PluginInstanceConfigurationSequence)
            else PluginInstanceConfigurationSequence(configuration)
            for configuration in configurations
        )

    @override
    @classmethod
    def _item_cls(
        cls,
    ) -> type[PluginInstanceConfigurationSequence[_PluginDefinitionT, _PluginT]]:
        return PluginInstanceConfigurationSequence

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(
            cls(
                [
                    next(  # type: ignore[list-item]
                        iter(PluginInstanceConfigurationSequence.samples())
                    ).configuration
                ]
            ),
            label="Default",
        )
