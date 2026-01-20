from collections.abc import Mapping
from typing import cast

import pytest
from typing_extensions import override

from betty.data.indicator.selector import Attr
from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.plugin.config import (
    CountableHumanFacingPluginDefinitionConfiguration,
    HumanFacingPluginDefinitionConfiguration,
    PluginConfiguration,
    PluginDefinitionConfiguration,
    PluginIdentifierKeyConfigurationMapping,
    PluginInstanceConfigurationMapping,
    PluginInstanceConfigurationSequence,
    PluginInstanceConfigurationSequenceSequence,
)
from betty.plugin.resolve import ResolvableId
from betty.portable import PortableData
from betty.test_utils.config import ConfigurationTestBase, DummyConfiguration
from betty.test_utils.config.collections import (
    ConfigurationCollectionTestBaseNewSut,
    ConfigurationCollectionTestBaseSutConfigurationKeys,
    ConfigurationCollectionTestBaseSutConfigurations,
)
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.plugin import (
    DummyPlugin,
    DummyPluginDefinition,
    DummyPluginFour,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)
from betty.test_utils.plugin.config import (
    ConfigurableDummyPlugin,
    ConfigurableDummyPluginDefinition,
    ConfigurableDummyPluginOne,
)
from betty.typing import Void


class TestPluginDefinitionConfiguration(
    ConfigurationTestBase[PluginDefinitionConfiguration]
):
    sut_cls = PluginDefinitionConfiguration

    async def test_load(self) -> None:
        plugin_id = "hello-world"
        portable: PortableData = {
            "id": plugin_id,
        }
        sut = PluginDefinitionConfiguration.load(portable)
        assert sut.id == plugin_id

    async def test_dump(self) -> None:
        plugin_id = "hello-world"
        sut = PluginDefinitionConfiguration(id=plugin_id)
        portable = sut.dump()
        assert isinstance(portable, dict)
        assert portable["id"] == plugin_id

    async def test_id(self) -> None:
        plugin_id = "hello-world"
        sut = PluginDefinitionConfiguration(id=plugin_id)
        assert sut.id == plugin_id


class TestHumanFacingPluginDefinitionConfiguration(
    ConfigurationTestBase[HumanFacingPluginDefinitionConfiguration]
):
    sut_cls = HumanFacingPluginDefinitionConfiguration

    async def test_load__with_undetermined_label(self) -> None:
        label = "Hello, world!"
        portable: PortableData = {
            "id": "hello-world",
            "label": label,
        }
        sut = HumanFacingPluginDefinitionConfiguration.load(portable)
        assert sut.label.localize(DEFAULT_LOCALIZER) == label

    async def test_load__with_expanded_label(self) -> None:
        label = "Hello, world!"
        portable: PortableData = {
            "id": "hello-world",
            "label": {
                DEFAULT_LOCALE_TAG: label,
            },
        }
        sut = HumanFacingPluginDefinitionConfiguration.load(portable)
        assert sut.label.localize(DEFAULT_LOCALIZER) == label

    async def test_load__with_undetermined_description(self) -> None:
        description = "Hello, world!"
        portable: PortableData = {
            "id": "hello-world",
            "label": "",
            "description": description,
        }
        sut = HumanFacingPluginDefinitionConfiguration.load(portable)
        assert sut.description is not None
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    async def test_load__with_expanded_description(self) -> None:
        description = "Hello, world!"
        portable: PortableData = {
            "id": "hello-world",
            "label": "",
            "description": {
                DEFAULT_LOCALE_TAG: description,
            },
        }
        sut = HumanFacingPluginDefinitionConfiguration.load(portable)
        assert sut.description is not None
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    async def test_dump__with_undetermined_label(self) -> None:
        label = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(id="hello-world", label=label)
        portable = sut.dump()
        assert isinstance(portable, dict)
        assert portable["label"] == label

    async def test_dump__with_expanded_label(self) -> None:
        label = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world", label=StaticTranslations({DEFAULT_LOCALE_TAG: label})
        )
        portable = sut.dump()
        assert isinstance(portable, dict)
        assert portable["label"] == {
            DEFAULT_LOCALE_TAG: label,
        }

    async def test_dump__with_undetermined_description(self) -> None:
        description = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world", label=DUMMY_LOCALIZABLE, description=description
        )
        portable = sut.dump()
        assert isinstance(portable, dict)
        assert portable["description"] == description

    async def test_dump__with_expanded_description(self) -> None:
        description = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world",
            label=DUMMY_LOCALIZABLE,
            description=StaticTranslations({DEFAULT_LOCALE_TAG: description}),
        )
        portable = sut.dump()
        assert isinstance(portable, dict)
        assert portable["description"] == {
            DEFAULT_LOCALE_TAG: description,
        }

    async def test_label(self) -> None:
        label = DUMMY_LOCALIZABLE
        sut = HumanFacingPluginDefinitionConfiguration(id="hello-world", label=label)
        assert sut.label is label

    async def test_description(self) -> None:
        description = DUMMY_LOCALIZABLE
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world", label=DUMMY_LOCALIZABLE, description=description
        )
        assert sut.description is description


class TestCountableHumanFacingPluginDefinitionConfiguration(
    ConfigurationTestBase[CountableHumanFacingPluginDefinitionConfiguration]
):
    sut_cls = CountableHumanFacingPluginDefinitionConfiguration

    async def test_load__with_undetermined_label(self) -> None:
        label_plural = "Hello, world!"
        label_countable = {
            DEFAULT_LOCALE_TAG: {
                "one": "{count} world",
                "other": "{count} worlds",
            }
        }
        portable: PortableData = {
            "id": "hello-world",
            "label": "-",
            "label_plural": label_plural,
            "label_countable": label_countable,
        }
        sut = CountableHumanFacingPluginDefinitionConfiguration.load(portable)
        assert sut.dump() == portable

    async def test_dump__with_undetermined_label(self) -> None:
        label_plural = "Hello, world!"
        label_countable = {
            DEFAULT_LOCALE_TAG: {
                "one": "{count} world",
                "other": "{count} worlds",
            }
        }
        sut = CountableHumanFacingPluginDefinitionConfiguration(
            id="-",
            label="-",
            label_plural=label_plural,
            label_countable=label_countable,
        )
        portable = sut.dump()
        assert isinstance(portable, dict)
        assert portable["label_plural"] == label_plural
        assert portable["label_countable"] == label_countable

    async def test_label_plural(self) -> None:
        label_plural = DUMMY_LOCALIZABLE
        sut = CountableHumanFacingPluginDefinitionConfiguration(
            id="-",
            label="-",
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.label_plural is label_plural

    async def test_label_countable(self) -> None:
        label_countable = DUMMY_COUNTABLE_LOCALIZABLE
        sut = CountableHumanFacingPluginDefinitionConfiguration(
            id="-", label="-", label_plural="-", label_countable=label_countable
        )
        assert sut.label_countable is label_countable


class TestPluginConfiguration(ConfigurationTestBase[PluginConfiguration]):
    sut_cls = PluginConfiguration

    def test_id(self) -> None:
        sut = PluginConfiguration[DummyPluginDefinition, DummyPlugin](
            DummyPluginOne.plugin()
        )
        assert sut.id == DummyPluginOne.plugin().id

    def test_configuration__with_configuration(self) -> None:
        configuration = DummyConfiguration()
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), configuration)
        assert sut.configuration is configuration

    def test_configuration__with_portable_configuration(self) -> None:
        configuration = DummyConfiguration().dump()
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), configuration)
        assert sut.configuration == sut.configuration
        assert sut.configuration == configuration

    def test_load__without_id(self) -> None:
        with pytest.raises(HumanFacingException):
            PluginConfiguration.load({})

    def test_load__minimal(self) -> None:
        sut = PluginConfiguration[DummyPluginDefinition, DummyPlugin].load(
            {"id": DummyPluginOne.plugin().id}
        )
        assert sut.id == DummyPluginOne.plugin().id
        assert sut.configuration is Void()

    def test_load__minimal_compact(self) -> None:
        sut = PluginConfiguration[DummyPluginDefinition, DummyPlugin].load(
            DummyPluginOne.plugin().id
        )
        assert sut.id == DummyPluginOne.plugin().id
        assert sut.configuration is Void()

    def test_load__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ].load(
            {
                "id": ConfigurableDummyPluginOne.plugin().id,
                "configuration": configuration,
            }
        )
        assert sut.id == ConfigurableDummyPluginOne.plugin().id
        assert sut.configuration == configuration

    def test_load_key(self) -> None:
        sut = PluginConfiguration[DummyPluginDefinition, DummyPlugin].load_key(
            {}, Attr("id"), DummyPluginOne.plugin().id
        )
        assert sut.id == DummyPluginOne.plugin().id
        assert sut.configuration == {}

    def test_load_key__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ].load_key(configuration, Attr("id"), ConfigurableDummyPluginOne.plugin().id)
        assert sut.id == ConfigurableDummyPluginOne.plugin().id
        assert sut.configuration == configuration

    def test_dump__minimal(self) -> None:
        sut = PluginConfiguration[ConfigurableDummyPluginDefinition, DummyPlugin](
            ConfigurableDummyPluginOne.plugin()
        )
        assert sut.dump() == ConfigurableDummyPluginOne.plugin().id

    def test_dump__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), DummyConfiguration(value))
        assert sut.dump() == {
            "id": ConfigurableDummyPluginOne.plugin().id,
            "configuration": {
                "value": value,
            },
        }

    def test_dump__with_portable_configuration(self) -> None:
        portable_configuration = {
            "value": "Hello, world!",
        }
        sut = PluginConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), portable_configuration)
        assert sut.dump() == {
            "id": ConfigurableDummyPluginOne.plugin().id,
            "configuration": portable_configuration,
        }

    def test_dump_key__minimal(self) -> None:
        sut = PluginConfiguration[ConfigurableDummyPluginDefinition, DummyPlugin](
            ConfigurableDummyPluginOne.plugin()
        )
        assert sut.dump_key(Attr("id")) == (ConfigurableDummyPluginOne.plugin().id, {})

    def test_dump_key__with_configuration(self) -> None:
        value = "Hello, world!"
        sut = PluginConfiguration[ConfigurableDummyPluginDefinition, DummyPlugin](
            ConfigurableDummyPluginOne.plugin(), DummyConfiguration(value)
        )
        assert sut.dump_key(Attr("id")) == (
            ConfigurableDummyPluginOne.plugin().id,
            {
                "configuration": {
                    "value": value,
                },
            },
        )

    def test_dump_key__with_portable_configuration(self) -> None:
        portable_configuration = {
            "value": "Hello, world!",
        }
        sut = PluginConfiguration[ConfigurableDummyPluginDefinition, DummyPlugin](
            ConfigurableDummyPluginOne.plugin(), portable_configuration
        )
        assert sut.dump_key(Attr("id")) == (
            ConfigurableDummyPluginOne.plugin().id,
            {"configuration": portable_configuration},
        )


class TestPluginInstanceConfigurationMapping(
    ConfigurationMappingTestBase[
        PluginInstanceConfigurationMapping,
        MachineName,
        ResolvableId[DummyPluginDefinition],
        PluginConfiguration[DummyPluginDefinition, DummyPlugin],
    ]
):
    sut_cls = PluginInstanceConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return (
            DummyPluginOne.plugin().id,
            DummyPluginTwo.plugin().id,
            DummyPluginThree.plugin().id,
            DummyPluginFour.plugin().id,
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PluginConfiguration[DummyPluginDefinition, DummyPlugin],
        MachineName,
        ResolvableId[DummyPluginDefinition],
    ]:
        return PluginInstanceConfigurationMapping

    @override
    @pytest.fixture
    def sut_configurations(
        self,
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            MachineName
        ],
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PluginConfiguration[DummyPluginDefinition, DummyPlugin]
    ]:
        return (
            PluginConfiguration(sut_configuration_keys[0]),
            PluginConfiguration(sut_configuration_keys[1]),
            PluginConfiguration(sut_configuration_keys[2]),
            PluginConfiguration(sut_configuration_keys[3]),
        )


class TestPluginIdentifierKeyConfigurationMapping:
    class _Sut(
        PluginIdentifierKeyConfigurationMapping[
            DummyPluginDefinition, DummyConfiguration
        ]
    ):
        @override
        def _dump_key(self, portable_item: PortableData, /) -> tuple[PortableData, str]:
            if isinstance(portable_item, str):
                return None, portable_item
            assert isinstance(portable_item, Mapping)
            return None, cast(str, portable_item["value"])  # ty:ignore[invalid-argument-type]

        @override
        def _get_key(self, configuration: DummyConfiguration, /) -> MachineName:
            assert configuration.value
            return configuration.value

        @override
        @classmethod
        def _load_key(
            cls, portable_item: PortableData, portable_key: str, /
        ) -> PortableData:
            return {"value": portable_key}

        @override
        @classmethod
        def _item_cls(cls) -> type[DummyConfiguration]:
            return DummyConfiguration

    def test___contains____with_plugin(self) -> None:
        item = DummyConfiguration(DummyPluginOne.plugin().id)
        sut = self._Sut([item])
        assert DummyPluginOne.plugin() in sut

    def test___contains____with_plugin_id(self) -> None:
        item = DummyConfiguration(DummyPluginOne.plugin().id)
        sut = self._Sut([item])
        assert DummyPluginOne.plugin().id in sut

    def test___getitem____with_plugin(self) -> None:
        item = DummyConfiguration(DummyPluginOne.plugin().id)
        sut = self._Sut([item])
        assert sut[DummyPluginOne.plugin()] is item

    def test___getitem____with_plugin_id(self) -> None:
        item = DummyConfiguration(DummyPluginOne.plugin().id)
        sut = self._Sut([item])
        assert sut[DummyPluginOne.plugin().id] is item


class TestPluginInstanceConfigurationSequence(
    ConfigurationSequenceTestBase[
        PluginInstanceConfigurationSequence,
        PluginConfiguration[DummyPluginDefinition, DummyPlugin],
    ]
):
    sut_cls = PluginInstanceConfigurationSequence

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PluginConfiguration[DummyPluginDefinition, DummyPlugin], int, int
    ]:
        return PluginInstanceConfigurationSequence

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PluginConfiguration[DummyPluginDefinition, DummyPlugin]
    ]:
        return (
            PluginConfiguration("my-first-plugin"),
            PluginConfiguration("my-second-plugin"),
            PluginConfiguration("my-third-plugin"),
            PluginConfiguration("my-fourth-plugin"),
        )


class TestPluginInstanceConfigurationSequenceSequence(
    ConfigurationSequenceTestBase[
        PluginInstanceConfigurationSequenceSequence[DummyPluginDefinition, DummyPlugin],
        PluginInstanceConfigurationSequence[DummyPluginDefinition, DummyPlugin],
    ]
):
    sut_cls = PluginInstanceConfigurationSequenceSequence

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PluginInstanceConfigurationSequence[DummyPluginDefinition, DummyPlugin],
        int,
        int,
    ]:
        return PluginInstanceConfigurationSequenceSequence

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PluginInstanceConfigurationSequence[DummyPluginDefinition, DummyPlugin]
    ]:
        return (
            PluginInstanceConfigurationSequence(
                PluginConfiguration[DummyPluginDefinition, DummyPlugin](
                    "my-first-plugin"
                )
            ),
            PluginInstanceConfigurationSequence(
                PluginConfiguration[DummyPluginDefinition, DummyPlugin](
                    "my-second-plugin"
                )
            ),
            PluginInstanceConfigurationSequence(
                PluginConfiguration[DummyPluginDefinition, DummyPlugin](
                    "my-third-plugin"
                )
            ),
            PluginInstanceConfigurationSequence(
                PluginConfiguration[DummyPluginDefinition, DummyPlugin](
                    "my-fourth-plugin"
                )
            ),
        )
