"""
Provide plugin configuration.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Generic, Self, TypeAlias, final

from typing_extensions import TypeVar, override

from betty.assertion import (
    OptionalField,
    RequiredField,
    assert_mapping,
    assert_or,
    assert_record,
)
from betty.config import Configuration
from betty.data import Data, Sample
from betty.data.aggregate.record import PortableRecord
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.aggregate.record.object.property import Optional, Property
from betty.data.indicator.selector import Attr
from betty.data.sample import Samples, Size
from betty.locale.localizable.gettext import _
from betty.locale.localizable.property import (
    CountableLocalizableProperty,
    LocalizableProperty,
)
from betty.machine_name import MachineName, MachineNameDefinition, assert_machine_name
from betty.plugin import Plugin, PluginDefinition
from betty.plugin.resolve import ResolvableId, resolve_definition, resolve_id
from betty.typing import Void

if TYPE_CHECKING:
    from betty.locale.localizable import CountableLocalizableLike, LocalizableLike
    from betty.portable import PortableData

_PluginT = TypeVar("_PluginT", bound=Plugin, default=Plugin)
_PluginDefinitionT = TypeVar(
    "_PluginDefinitionT", bound=PluginDefinition, default=PluginDefinition
)


class PluginDefinitionConfiguration(
    Data[ObjectDefinition["PluginDefinitionConfiguration"]]
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


class HumanFacingPluginDefinitionConfiguration(PluginDefinitionConfiguration):
    """
    Configure a :py:class:`betty.definition.human_facing.HumanFacingDefinition`.

    .. data:: betty.plugin.config:HumanFacingPluginDefinitionConfiguration
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
        self.label = label
        self.description = description


class CountableHumanFacingPluginDefinitionConfiguration(
    HumanFacingPluginDefinitionConfiguration
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
        label_plural: LocalizableLike,
        label_countable: CountableLocalizableLike,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.label_plural = label_plural
        self.label_countable = label_countable


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
        configuration: Data | Configuration | PortableData | Void = Void(),  # noqa: B008
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
    def configuration(self) -> Data | Configuration | PortableData | Void:
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

    def _dump_configuration(
        self, configuration: Data | Configuration | PortableData
    ) -> PortableData:
        if isinstance(configuration, Configuration):
            return configuration.dump()
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


ResolvablePluginConfigurations: TypeAlias = (
    ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT]
    | Iterable[ResolvablePluginConfiguration[_PluginDefinitionT, _PluginT]]
)


def resolve_plugin_configurations(
    plugin_configurations: ResolvablePluginConfigurations[_PluginDefinitionT, _PluginT],
) -> Iterable[PluginConfiguration[_PluginDefinitionT, _PluginT]]:
    """
    Resolve a value to an iterable of plugin configurations.
    """
    if isinstance(plugin_configurations, PluginConfiguration):
        return (plugin_configurations,)
    if (
        isinstance(plugin_configurations, (str, PluginDefinition))
        or isinstance(plugin_configurations, type)
        and issubclass(plugin_configurations, Plugin)
    ):
        return (resolve_plugin_configuration(plugin_configurations),)  # ty:ignore[invalid-return-type]
    return map(resolve_plugin_configuration, plugin_configurations)  # ty:ignore[invalid-argument-type]
