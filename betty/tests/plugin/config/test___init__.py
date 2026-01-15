from collections.abc import Mapping
from typing import cast

import pytest
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.plugin.config import (
    CountableHumanFacingPluginDefinitionConfiguration,
    HumanFacingPluginDefinitionConfiguration,
    PluginDefinitionConfiguration,
    PluginIdentifierKeyConfigurationMapping,
    PluginInstanceConfiguration,
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
        serialized = sut.dump()
        assert isinstance(serialized, dict)
        assert serialized["id"] == plugin_id

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
        serialized = sut.dump()
        assert isinstance(serialized, dict)
        assert serialized["label"] == label

    async def test_dump__with_expanded_label(self) -> None:
        label = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world", label=StaticTranslations({DEFAULT_LOCALE_TAG: label})
        )
        serialized = sut.dump()
        assert isinstance(serialized, dict)
        assert serialized["label"] == {
            DEFAULT_LOCALE_TAG: label,
        }

    async def test_dump__with_undetermined_description(self) -> None:
        description = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world", label=DUMMY_LOCALIZABLE, description=description
        )
        serialized = sut.dump()
        assert isinstance(serialized, dict)
        assert serialized["description"] == description

    async def test_dump__with_expanded_description(self) -> None:
        description = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world",
            label=DUMMY_LOCALIZABLE,
            description=StaticTranslations({DEFAULT_LOCALE_TAG: description}),
        )
        serialized = sut.dump()
        assert isinstance(serialized, dict)
        assert serialized["description"] == {
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
            "label_countable": label_countable,  # type: ignore[dict-item]
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
        serialized = sut.dump()
        assert isinstance(serialized, dict)
        assert serialized["label_plural"] == label_plural
        assert serialized["label_countable"] == label_countable

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


class TestPluginInstanceConfiguration(
    ConfigurationTestBase[PluginInstanceConfiguration]
):
    sut_cls = PluginInstanceConfiguration

    def test_id(self) -> None:
        sut = PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin](
            DummyPluginOne.plugin()
        )
        assert sut.id == DummyPluginOne.plugin().id

    def test_configuration__with_configuration(self) -> None:
        configuration = DummyConfiguration()
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), configuration)
        assert sut.configuration is configuration

    def test_configuration__with_dump(self) -> None:
        configuration = DummyConfiguration().dump()
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), configuration)
        assert sut.configuration == sut.configuration
        assert sut.configuration == configuration

    def test_load__without_id(self) -> None:
        with pytest.raises(HumanFacingException):
            PluginInstanceConfiguration.load({})

    def test_load__minimal(self) -> None:
        sut = PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin].load(
            {"id": DummyPluginOne.plugin().id}
        )
        assert sut.id == DummyPluginOne.plugin().id

    def test_load__with_configuration(self) -> None:
        configuration: PortableData = {
            "check": True,
        }
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ].load(
            {
                "id": ConfigurableDummyPluginOne.plugin().id,
                "configuration": configuration,
            }
        )
        assert sut.configuration == configuration

    def test_dump__should_dump_minimal(self) -> None:
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, DummyPlugin
        ](ConfigurableDummyPluginOne.plugin())
        assert sut.dump() == ConfigurableDummyPluginOne.plugin().id

    def test_dump__should_dump_configuration(self) -> None:
        value = "Hello, world!"
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin(), DummyConfiguration(value))
        expected = {
            "id": ConfigurableDummyPluginOne.plugin().id,
            "configuration": {
                "value": value,
            },
        }
        assert sut.dump() == expected


class TestPluginInstanceConfigurationMapping(
    ConfigurationMappingTestBase[
        PluginInstanceConfigurationMapping,
        MachineName,
        ResolvableId[DummyPluginDefinition],
        PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin],
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
        PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin],
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
        PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin]
    ]:
        return (
            PluginInstanceConfiguration(sut_configuration_keys[0]),
            PluginInstanceConfiguration(sut_configuration_keys[1]),
            PluginInstanceConfiguration(sut_configuration_keys[2]),
            PluginInstanceConfiguration(sut_configuration_keys[3]),
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
            return None, cast(str, portable_item["value"])

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
        PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin],
    ]
):
    sut_cls = PluginInstanceConfigurationSequence

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin], int, int
    ]:
        return PluginInstanceConfigurationSequence

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin]
    ]:
        return (
            PluginInstanceConfiguration("my-first-plugin"),
            PluginInstanceConfiguration("my-second-plugin"),
            PluginInstanceConfiguration("my-third-plugin"),
            PluginInstanceConfiguration("my-fourth-plugin"),
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
                PluginInstanceConfiguration("my-first-plugin")
            ),
            PluginInstanceConfigurationSequence(
                PluginInstanceConfiguration("my-second-plugin")
            ),
            PluginInstanceConfigurationSequence(
                PluginInstanceConfiguration("my-third-plugin")
            ),
            PluginInstanceConfigurationSequence(
                PluginInstanceConfiguration("my-fourth-plugin")
            ),
        )
