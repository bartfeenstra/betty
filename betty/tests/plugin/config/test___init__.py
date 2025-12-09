from collections.abc import Mapping
from typing import cast

import pytest
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.locale import DEFAULT_LOCALE_TAG
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.plugin.config import (
    CountableHumanFacingPluginDefinitionConfiguration,
    HumanFacingPluginDefinitionConfiguration,
    PluginDefinitionConfiguration,
    PluginIdentifierKeyConfigurationMapping,
    PluginInstanceConfiguration,
    PluginInstanceConfigurationMapping,
    PluginInstanceConfigurationSequence,
)
from betty.plugin.resolve import ResolvableId
from betty.serde.dump import Dump
from betty.test_utils.config import DummyConfiguration
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


class TestPluginDefinitionConfiguration:
    async def test_load(self) -> None:
        plugin_id = "hello-world"
        dump: Dump = {
            "id": plugin_id,
        }
        sut = PluginDefinitionConfiguration.load(dump)
        assert sut.id == plugin_id

    async def test_dump(self) -> None:
        plugin_id = "hello-world"
        sut = PluginDefinitionConfiguration(id=plugin_id)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["id"] == plugin_id

    async def test_id(self) -> None:
        plugin_id = "hello-world"
        sut = PluginDefinitionConfiguration(id=plugin_id)
        assert sut.id == plugin_id


class TestHumanFacingPluginDefinitionConfiguration:
    async def test_load__with_undetermined_label(self) -> None:
        label = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": label,
        }
        sut = HumanFacingPluginDefinitionConfiguration.load(dump)
        assert sut.label.localize(DEFAULT_LOCALIZER) == label

    async def test_load__with_expanded_label(self) -> None:
        label = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": {
                DEFAULT_LOCALE_TAG: label,
            },
        }
        sut = HumanFacingPluginDefinitionConfiguration.load(dump)
        assert sut.label.localize(DEFAULT_LOCALIZER) == label

    async def test_load__with_undetermined_description(self) -> None:
        description = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "description": description,
        }
        sut = HumanFacingPluginDefinitionConfiguration.load(dump)
        assert sut.description is not None
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    async def test_load__with_expanded_description(self) -> None:
        description = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "description": {
                DEFAULT_LOCALE_TAG: description,
            },
        }
        sut = HumanFacingPluginDefinitionConfiguration.load(dump)
        assert sut.description is not None
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    async def test_dump__with_undetermined_label(self) -> None:
        label = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(id="hello-world", label=label)
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["label"] == label

    async def test_dump__with_expanded_label(self) -> None:
        label = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world", label=StaticTranslations({DEFAULT_LOCALE_TAG: label})
        )
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["label"] == {
            DEFAULT_LOCALE_TAG: label,
        }

    async def test_dump__with_undetermined_description(self) -> None:
        description = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world", label=DUMMY_LOCALIZABLE, description=description
        )
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["description"] == description

    async def test_dump__with_expanded_description(self) -> None:
        description = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world",
            label=DUMMY_LOCALIZABLE,
            description=StaticTranslations({DEFAULT_LOCALE_TAG: description}),
        )
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["description"] == {
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


class TestCountableHumanFacingPluginDefinitionConfiguration:
    async def test_load__with_undetermined_label(self) -> None:
        label_plural = "Hello, world!"
        label_countable = {
            DEFAULT_LOCALE_TAG: {
                "one": "{count} world",
                "other": "{count} worlds",
            }
        }
        dump: Dump = {
            "id": "hello-world",
            "label": "-",
            "label_plural": label_plural,
            "label_countable": label_countable,  # type: ignore[dict-item]
        }
        sut = CountableHumanFacingPluginDefinitionConfiguration.load(dump)
        assert sut.dump() == dump

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
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["label_plural"] == label_plural
        assert dump["label_countable"] == label_countable

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


class TestPluginInstanceConfiguration:
    def test___init____with_configuration(self):
        value = "Hello, world!"
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin, DummyConfiguration(value))
        assert sut.configuration == {"value": value}

    def test___init____with_configuration_dump(self):
        configuration: Dump = {
            "value": "Hello, world!",
        }
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin, configuration)
        assert sut.configuration == configuration

    def test_id(self) -> None:
        sut = PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin](
            DummyPluginOne.plugin
        )
        assert sut.id == DummyPluginOne.plugin.id

    def test_configuration__with_configuration(self) -> None:
        configuration = DummyConfiguration()
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin, configuration)
        assert sut.configuration == sut.configuration
        assert sut.configuration == configuration.dump()

    def test_configuration__with_dump(self) -> None:
        configuration = DummyConfiguration().dump()
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin, configuration)
        assert sut.configuration == sut.configuration
        assert sut.configuration == configuration

    def test_load__without_id(self) -> None:
        with pytest.raises(HumanFacingException):
            PluginInstanceConfiguration.load({})

    def test_load__minimal(self) -> None:
        sut = PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin].load(
            {"id": DummyPluginOne.plugin.id}
        )
        assert sut.id == DummyPluginOne.plugin.id

    def test_load__with_configuration(self) -> None:
        configuration: Dump = {
            "check": True,
        }
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ].load(
            {
                "id": ConfigurableDummyPluginOne.plugin.id,
                "configuration": configuration,
            }
        )
        assert sut.configuration == configuration

    def test_dump__should_dump_minimal(self) -> None:
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, DummyPlugin
        ](ConfigurableDummyPluginOne.plugin)
        assert sut.dump() == ConfigurableDummyPluginOne.plugin.id

    def test_dump__should_dump_configuration(self) -> None:
        value = "Hello, world!"
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin, DummyConfiguration(value))
        expected = {
            "id": ConfigurableDummyPluginOne.plugin.id,
            "configuration": {
                "value": value,
            },
        }
        assert sut.dump() == expected


class TestPluginInstanceConfigurationMapping(
    ConfigurationMappingTestBase[
        MachineName,
        ResolvableId[DummyPluginDefinition, DummyPlugin],
        PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin],
    ]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return (
            DummyPluginOne.plugin.id,
            DummyPluginTwo.plugin.id,
            DummyPluginThree.plugin.id,
            DummyPluginFour.plugin.id,
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin],
        MachineName,
        ResolvableId[DummyPluginDefinition, DummyPlugin],
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
            DummyPluginDefinition, DummyPlugin, DummyConfiguration
        ]
    ):
        @override
        def _dump_key(self, item_dump: Dump, /) -> tuple[Dump, str]:
            if isinstance(item_dump, str):
                return None, item_dump
            assert isinstance(item_dump, Mapping)
            return None, cast(str, item_dump["value"])

        @override
        def _get_key(self, configuration: DummyConfiguration, /) -> MachineName:
            assert configuration.value
            return configuration.value

        @override
        @classmethod
        def _load_key(cls, item_dump: Dump, key_dump: str, /) -> Dump:
            return {"value": key_dump}

        @override
        @classmethod
        def _load_item(cls, dump: Dump, /) -> DummyConfiguration:
            raise NotImplementedError

    def test___contains____with_plugin(self) -> None:
        item = DummyConfiguration(DummyPluginOne.plugin.id)
        sut = self._Sut([item])
        assert DummyPluginOne.plugin in sut

    def test___contains____with_plugin_id(self) -> None:
        item = DummyConfiguration(DummyPluginOne.plugin.id)
        sut = self._Sut([item])
        assert DummyPluginOne.plugin.id in sut

    def test___getitem____with_plugin(self) -> None:
        item = DummyConfiguration(DummyPluginOne.plugin.id)
        sut = self._Sut([item])
        assert sut[DummyPluginOne.plugin] is item

    def test___getitem____with_plugin_id(self) -> None:
        item = DummyConfiguration(DummyPluginOne.plugin.id)
        sut = self._Sut([item])
        assert sut[DummyPluginOne.plugin.id] is item


class TestPluginInstanceConfigurationSequence(
    ConfigurationSequenceTestBase[
        PluginInstanceConfiguration[DummyPluginDefinition, DummyPlugin]
    ]
):
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
