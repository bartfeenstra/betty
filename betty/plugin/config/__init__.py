"""
Provide plugin configuration.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection, Iterable, MutableMapping, Sequence
from typing import TYPE_CHECKING, Any, Generic, Self, TypeAlias, cast, final

from typing_extensions import TypeVar, override

from betty.assertion import (
    Field,
    OptionalField,
    RequiredField,
    assert_or,
    assert_record,
)
from betty.config import Configuration
from betty.config.collections import ConfigurationCollection, ConfigurationKey
from betty.config.collections.mapping import ConfigurationMapping
from betty.config.collections.sequence import ConfigurationSequence
from betty.data import Sample
from betty.data.aggregate.record import PortableRecord
from betty.data.aggregate.record.object.property import Optional
from betty.data.indicator.selector import Attr
from betty.data.sample import Samples, Size
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.assertion import (
    assert_load_countable_localizable,
    assert_load_localizable,
)
from betty.locale.localizable.ensure import (
    ensure_countable_localizable,
    ensure_localizable,
)
from betty.locale.localizable.gettext import _
from betty.locale.localizable.portable import (
    dump_countable_localizable,
    dump_localizable,
)
from betty.locale.localizable.property import (
    CountableLocalizableProperty,
    LocalizableProperty,
)
from betty.locale.localizable.static import CountableStaticTranslations
from betty.machine_name import MachineName, assert_machine_name
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.resolve import ResolvableId, resolve_id
from betty.typing import Void

if TYPE_CHECKING:
    from betty.locale.localizable import CountableLocalizableLike, LocalizableLike
    from betty.portable import PortableData, PortableMapping

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
        id: MachineName,  # noqa: A002
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
    def load(cls, portable: PortableData, /) -> Self:
        return cls(**assert_record(*cls.fields())(portable))

    @classmethod
    def fields(cls) -> Collection[Field[Any, Any]]:
        """
        The configuration fields.
        """
        return [
            RequiredField("id", assert_machine_name()),
        ]

    @override
    def dump(self) -> PortableMapping:
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
    def samples(cls) -> Samples:
        return Samples([lambda: Sample(cls(id="my-custom-plugin"), label="Default")])


class HumanFacingPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.definition.human_facing.HumanFacingDefinition`.

    .. configuration:: betty.plugin.config:HumanFacingPluginDefinitionConfiguration
    """

    label = LocalizableProperty(label=_("Label"))
    description = Optional(LocalizableProperty(label=_("Description")))

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
    def dump(self) -> PortableMapping:
        portable = super().dump()
        portable["label"] = dump_localizable(self.label)
        if self.description is not None:
            portable["description"] = dump_localizable(self.description)
        return portable

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
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    cls(id="my-custom-plugin", label="My Custom Plugin"),
                    label="Minimal",
                    size=Size.MINIMAL,
                ),
                lambda: Sample(
                    cls(
                        id="my-custom-plugin",
                        label="My Custom Plugin",
                        description="My Custom Plugin is the best plugin for your needs.",
                    ),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


class CountableHumanFacingPluginDefinitionConfiguration(
    HumanFacingPluginDefinitionConfiguration
):
    """
    Configure a :py:class:`betty.definition.human_facing.CountableHumanFacingDefinition`.

    .. configuration:: betty.plugin.config:CountableHumanFacingPluginDefinitionConfiguration
    """

    label_plural = LocalizableProperty(label=_("Label (plural)"))
    label_countable = CountableLocalizableProperty(label=_("Label (countable)"))

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
    def dump(self) -> PortableMapping:
        portable = super().dump()
        portable["label_plural"] = dump_localizable(self.label_plural)
        portable["label_countable"] = dump_countable_localizable(self.label_countable)
        return portable

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
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
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
                    size=Size.MINIMAL,
                ),
                lambda: Sample(
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
                    size=Size.FULL,
                ),
            ]
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
        cls, portable_item: PortableData, portable_key: str, /
    ) -> PortableData:
        assert isinstance(portable_item, MutableMapping)
        portable_item["id"] = portable_key  # ty:ignore[invalid-assignment]
        return portable_item

    @override
    def _dump_key(self, portable_item: PortableData, /) -> tuple[PortableData, str]:
        assert isinstance(portable_item, MutableMapping)
        return portable_item, cast(str, portable_item.pop("id"))  # ty:ignore[invalid-argument-type]


@final
class PluginConfiguration(
    Configuration, PortableRecord[Attr], Generic[_PluginDefinitionT, _PluginT]
):
    """
    Configure a single plugin instance.

    Use this with :py:class:`betty.plugin.data.PluginConfigurationDefinition` to provide defined data.

    .. configuration:: betty.plugin.config:PluginConfiguration
    """

    def __init__(
        self,
        id: ResolvableId[_PluginDefinitionT],  # noqa: A002
        configuration: Configuration | PortableData | Void = Void(),  # noqa: B008
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
    def configuration(self) -> Configuration | PortableData | Void:
        """
        Get the plugin's own configuration.
        """
        return self._configuration

    @override
    @classmethod
    def load(cls, portable: PortableData, /) -> Self:
        id_assertion = assert_machine_name()
        record = assert_or(
            id_assertion | (lambda plugin_id: {"id": plugin_id}),
            assert_record(
                RequiredField("id", id_assertion),
                OptionalField("configuration"),
            ),
        )(portable)
        return cls(record["id"], record.get("configuration", Void()))

    @override
    @classmethod
    def load_key(cls, portable: PortableData, key: Attr, portable_key: str, /) -> Self:
        return cls.load({"id": portable_key, "configuration": portable})

    @override
    def dump(self) -> PortableData:
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
    def dump_key(self, key: Attr, /) -> tuple[str, PortableData]:
        return self.id, {} if self.configuration is Void() else {
            "configuration": self.configuration.dump()
            if isinstance(self.configuration, Configuration)
            else self.configuration,
        }

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    PluginConfiguration("my-first-plugin-id"),
                    label="Minimal",
                    size=Size.MINIMAL,
                ),
                lambda: Sample(
                    PluginConfiguration(
                        "my-first-plugin-id",
                        {
                            "configuration-key": "configuration-value",
                        },
                    ),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


ShorthandPluginInstanceConfigurationSequence: TypeAlias = (
    PluginConfiguration[_PluginDefinitionT, _PluginT]
    | Iterable[PluginConfiguration[_PluginDefinitionT, _PluginT]]
)


class _PluginInstanceConfigurationCollection(
    ConfigurationCollection[
        _ConfigurationKeyT,
        _ResolvableConfigurationKeyT,
        PluginConfiguration[_PluginDefinitionT, _PluginT],
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
        if isinstance(configurations, PluginConfiguration):
            configurations = [configurations]
        super().__init__(configurations)

    @override
    @classmethod
    def _item_cls(
        cls,
    ) -> type[PluginConfiguration[_PluginDefinitionT, _PluginT]]:
        return PluginConfiguration  # ty:ignore[invalid-return-type]


class PluginInstanceConfigurationMapping(
    _PluginInstanceConfigurationCollection[
        MachineName, ResolvableId[_PluginDefinitionT], _PluginDefinitionT, _PluginT
    ],
    PluginIdentifierKeyConfigurationMapping[
        _PluginDefinitionT,
        PluginConfiguration[_PluginDefinitionT, _PluginT],
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
        configuration: PluginConfiguration[_PluginDefinitionT, _PluginT],
        /,
    ) -> MachineName:
        return configuration.id

    @override
    @classmethod
    def _load_key(
        cls, portable_item: PortableData, portable_key: str, /
    ) -> PortableData:
        if not portable_item:
            return portable_key
        assert isinstance(portable_item, MutableMapping)
        portable_item["id"] = portable_key  # ty:ignore[invalid-assignment]
        return portable_item

    @override
    def _dump_key(self, portable_item: PortableData, /) -> tuple[PortableData, str]:
        if isinstance(portable_item, str):
            return {}, portable_item
        assert isinstance(portable_item, MutableMapping)
        return portable_item, cast(
            str,
            portable_item.pop(
                "id",  # ty:ignore[invalid-argument-type]
            ),
        )

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls([PluginConfiguration.samples().get(Size.FULL).data]),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


@final
class PluginInstanceConfigurationSequence(
    _PluginInstanceConfigurationCollection[int, int, _PluginDefinitionT, _PluginT],
    ConfigurationSequence[PluginConfiguration[_PluginDefinitionT, _PluginT]],
):
    """
    A sequence of plugin instance configurations.

    .. configuration:: betty.plugin.config:PluginInstanceConfigurationSequence
    """

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(cls(), label="Minimal", size=Size.MINIMAL),
                lambda: Sample(
                    cls([PluginConfiguration.samples().get(Size.FULL).data]),
                    label="Full",
                    size=Size.FULL,
                ),
            ]
        )


ShorthandPluginInstanceConfigurationSequenceSequence: TypeAlias = (
    Iterable[ShorthandPluginInstanceConfigurationSequence[_PluginDefinitionT, _PluginT]]
    | PluginConfiguration[_PluginDefinitionT, _PluginT]
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
        if isinstance(configurations, PluginConfiguration):
            configurations = [PluginInstanceConfigurationSequence([configurations])]  # ty:ignore[invalid-assignment]
        super().__init__(configurations)

    @override
    @classmethod
    def _item_cls(
        cls,
    ) -> type[PluginInstanceConfigurationSequence[_PluginDefinitionT, _PluginT]]:
        return PluginInstanceConfigurationSequence[_PluginDefinitionT, _PluginT]

    @override
    @classmethod
    def samples(cls) -> Samples:
        return Samples(
            [
                lambda: Sample(
                    cls(
                        [next(iter(PluginInstanceConfigurationSequence.samples())).data]
                    ),
                    label="Default",
                )
            ]
        )
