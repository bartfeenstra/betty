"""
Provide plugin configuration.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, MutableMapping, MutableSequence
from typing import TYPE_CHECKING, Any, Generic, Self, TypeAlias, final

from typing_extensions import TypeVar, override

from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_mapping,
    assert_or,
    assert_record,
)
from betty.data import Data
from betty.data.aggregate.record import PortableRecord
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Optional, Property
from betty.data.indicator.selector import Attr
from betty.locale.localizable.gettext import _
from betty.locale.localizable.property import (
    CountableLocalizableProperty,
    LocalizableProperty,
)
from betty.machine_name import MachineName, MachineNameDefinition, assert_machine_name
from betty.plugin import (
    Plugin,
    PluginDefinition,
    ResolvableId,
    resolve_definition,
    resolve_id,
)
from betty.sample import Samplable, Sample, Samples, Size
from betty.typing import Void

if TYPE_CHECKING:
    from betty.locale.localizable import (
        ResolvableCountableLocalizable,
        ResolvableLocalizable,
    )
    from betty.portable import PortableData
    from betty.service.level import ServiceLevel

_T = TypeVar("_T")
_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class PluginDefinitionConfiguration(
    Data[ObjectDefinition["PluginDefinitionConfiguration"]],
    ABC,
    Generic[_PluginDefinitionT],
):
    """
    Configure a :py:class:`betty.plugin.PluginDefinition`.

    .. data:: betty.plugin.config:PluginDefinitionConfiguration
    """

    id = Property(
        MachineNameDefinition(), label=_("Plugin ID"), resolver=assert_machine_name()
    )
    """
    The plugin ID.
    """

    def __init__(
        self,
        *,
        id: MachineName,  # noqa: A002
    ):
        super().__init__()
        self.id = id

    @abstractmethod
    def new_plugin(self) -> _PluginDefinitionT:
        """
        Create a new plugin from this configuration.
        """


class HumanFacingPluginDefinitionConfiguration(
    PluginDefinitionConfiguration[_PluginDefinitionT]
):
    """
    Configure a :py:class:`betty.definition.human_facing.HumanFacingDefinition`.

    .. data:: betty.plugin.config:HumanFacingPluginDefinitionConfiguration
    """

    label = LocalizableProperty(label=_("Label"))
    description = Optional(LocalizableProperty(label=_("Description")))

    def __init__(
        self,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label = label
        self.description = description


class CountableHumanFacingPluginDefinitionConfiguration(
    HumanFacingPluginDefinitionConfiguration[_PluginDefinitionT]
):
    """
    Configure a :py:class:`betty.definition.human_facing.CountableHumanFacingDefinition`.

    .. data:: betty.plugin.config:CountableHumanFacingPluginDefinitionConfiguration
    """

    label_plural = LocalizableProperty(label=_("Label (plural)"))
    label_countable = CountableLocalizableProperty(label=_("Label (countable)"))

    def __init__(
        self,
        *,
        label_plural: ResolvableLocalizable,
        label_countable: ResolvableCountableLocalizable,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label_plural = label_plural
        self.label_countable = label_countable


@final
class PluginConfiguration(
    PortableRecord[Attr], Samplable, Generic[_PluginDefinitionT, _PluginT]
):
    """
    Configure a single plugin instance.

    Use this with :py:class:`betty.plugin.data.PluginConfigurationDefinition` to provide defined data.
    """

    def __init__(
        self,
        id: ResolvableId[_PluginDefinitionT],  # noqa: A002
        configuration: Data | PortableData | Void = Void(),  # noqa: B008
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
    def configuration(self) -> Data | PortableData | Void:
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
        return cls.load({**assert_mapping()(portable), "id": portable_key})

    def _dump_configuration(self, configuration: Data | PortableData) -> PortableData:
        if isinstance(configuration, Data):
            return configuration.data().porter.dump(configuration)  # ty:ignore[invalid-argument-type]
        return configuration

    @override
    def dump(self) -> PortableData:
        configuration = self.configuration
        if isinstance(configuration, Void):
            return self._id
        return {
            "id": self._id,
            "configuration": self._dump_configuration(configuration),
        }

    @override
    def dump_key(self, key: Attr, /) -> tuple[str, PortableData]:
        return self.id, {} if self.configuration is Void() else {
            "configuration": self._dump_configuration(self.configuration),  # ty:ignore[invalid-argument-type]
        }

    async def new_plugin(
        self, services: ServiceLevel, plugin_type: type[_PluginDefinitionT], /
    ) -> _PluginT:
        """
        Create a new instance of the configured plugin.
        """
        return await services.factory.new(
            (await services.plugins.plugins(plugin_type))[self.id].cls,
            self.configuration,
        )

    @override
    @classmethod
    def samples(cls) -> Samples[Self]:
        return Samples(
            [
                lambda: Sample(
                    cls("my-first-plugin-id"),
                    label="Minimal",
                    size=Size.MINIMAL,
                ),
                lambda: Sample(
                    cls(
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


ResolvablePluginConfiguration: TypeAlias = (
    ResolvableId[_PluginDefinitionT] | PluginConfiguration[_PluginDefinitionT, _PluginT]
)


def resolve_plugin_configuration(
    plugin_configuration: ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT],
) -> PluginConfiguration[_PluginDefinitionT, _PluginT]:
    """
    Resolve a value to a plugin configuration.
    """
    if isinstance(plugin_configuration, PluginConfiguration):
        return plugin_configuration
    if isinstance(plugin_configuration, str):
        return PluginConfiguration(plugin_configuration)
    return PluginConfiguration(resolve_definition(plugin_configuration).id)  # ty:ignore[invalid-argument-type]


ResolvablePluginConfigurationSequence: TypeAlias = (
    ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT]
    | Iterable[ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT]]
)


def resolve_plugin_configuration_sequence(
    plugin_configurations: ResolvablePluginConfigurationSequence[
        _PluginDefinitionT, _PluginT
    ],
) -> MutableSequence[PluginConfiguration[_PluginDefinitionT, _PluginT]]:
    """
    Resolve a value to a sequence of plugin configurations.
    """
    if isinstance(plugin_configurations, PluginConfiguration):
        return [plugin_configurations]
    if (
        isinstance(plugin_configurations, (str, PluginDefinition))
        or isinstance(plugin_configurations, type)
        and issubclass(plugin_configurations, Plugin)
    ):
        return [resolve_plugin_configuration(plugin_configurations)]  # ty:ignore[invalid-argument-type]
    return list(map(resolve_plugin_configuration, plugin_configurations))  # ty:ignore[invalid-argument-type]


def resolve_plugin_configuration_mapping(
    plugin_configurations: Mapping[
        _T, ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT]
    ],
) -> MutableMapping[_T, PluginConfiguration[_PluginDefinitionT, _PluginT]]:
    """
    Resolve a value to a mapping of plugin configurations.
    """
    return {
        key: resolve_plugin_configuration(plugin_configuration)
        for key, plugin_configuration in plugin_configurations.items()
    }
