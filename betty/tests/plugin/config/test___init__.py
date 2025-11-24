from collections.abc import Mapping
from typing import cast

import pytest
from typing_extensions import override

from betty.exception import HumanFacingException
from betty.factory import new_target
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable import Plain, StaticTranslations
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.plugin.config import (
    HumanFacingPluginDefinitionConfiguration,
    PluginDefinitionConfiguration,
    PluginIdentifierKeyConfigurationMapping,
    PluginInstanceConfiguration,
    PluginInstanceConfigurationMapping,
    PluginInstanceConfigurationSequence,
)
from betty.plugin.repository.static import StaticPluginRepository
from betty.serde.dump import Dump
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.config.collections import (
    ConfigurationCollectionTestBaseNewSut,
    ConfigurationCollectionTestBaseSutConfigurationKeys,
    ConfigurationCollectionTestBaseSutConfigurations,
)
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.test_utils.exception import raises_error
from betty.test_utils.plugin import (
    DUMMY_PLUGIN_FOUR,
    DUMMY_PLUGIN_ONE,
    DUMMY_PLUGIN_THREE,
    DUMMY_PLUGIN_TWO,
    DummyPluginDefinition,
)
from betty.test_utils.plugin.classed import (
    ClassedDummyPlugin,
    ClassedDummyPluginDefinition,
    ClassedDummyPluginOne,
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
        sut = PluginDefinitionConfiguration(id="-")
        sut.load(dump)
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
        sut = HumanFacingPluginDefinitionConfiguration(id="-", label="")
        sut.load(dump)
        assert sut.label.localize(DEFAULT_LOCALIZER) == label

    async def test_load__with_expanded_label(self) -> None:
        label = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": {
                DEFAULT_LOCALE: label,
            },
        }
        sut = HumanFacingPluginDefinitionConfiguration(id="-", label="")
        sut.load(dump)
        assert sut.label.localize(DEFAULT_LOCALIZER) == label

    async def test_load__with_undetermined_description(self) -> None:
        description = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "description": description,
        }
        sut = HumanFacingPluginDefinitionConfiguration(id="-", label="")
        sut.load(dump)
        assert sut.description is not None
        assert sut.description.localize(DEFAULT_LOCALIZER) == description

    async def test_load__with_expanded_description(self) -> None:
        description = "Hello, world!"
        dump: Dump = {
            "id": "hello-world",
            "label": "",
            "description": {
                DEFAULT_LOCALE: description,
            },
        }
        sut = HumanFacingPluginDefinitionConfiguration(id="-", label="")
        sut.load(dump)
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
            id="hello-world", label=StaticTranslations({DEFAULT_LOCALE: label})
        )
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["label"] == {
            DEFAULT_LOCALE: label,
        }

    async def test_dump__with_undetermined_description(self) -> None:
        description = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world", label="", description=description
        )
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["description"] == description

    async def test_dump__with_expanded_description(self) -> None:
        description = "Hello, world!"
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world",
            label="",
            description=StaticTranslations({DEFAULT_LOCALE: description}),
        )
        dump = sut.dump()
        assert isinstance(dump, dict)
        assert dump["description"] == {
            DEFAULT_LOCALE: description,
        }

    async def test_label(self) -> None:
        label = Plain("")
        sut = HumanFacingPluginDefinitionConfiguration(id="hello-world", label=label)
        assert sut.label is label

    async def test_description(self) -> None:
        description = Plain("")
        sut = HumanFacingPluginDefinitionConfiguration(
            id="hello-world", label="", description=description
        )
        assert sut.description is description


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
        sut = PluginInstanceConfiguration[
            ClassedDummyPluginDefinition, ClassedDummyPlugin
        ](ClassedDummyPluginOne.plugin)
        assert sut.id == ClassedDummyPluginOne.plugin.id

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
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin)
        with raises_error(error_type=HumanFacingException):
            sut.load({})

    def test_load__minimal(self) -> None:
        sut = PluginInstanceConfiguration[
            ClassedDummyPluginDefinition, ClassedDummyPlugin
        ](ClassedDummyPluginOne.plugin)
        sut.load({"id": ClassedDummyPluginOne.plugin.id})
        assert sut.id == ClassedDummyPluginOne.plugin.id

    def test_load__with_configuration(self) -> None:
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin)
        configuration: Dump = {
            "check": True,
        }
        sut.load(
            {
                "id": ConfigurableDummyPluginOne.plugin.id,
                "configuration": configuration,
            }
        )
        assert sut.configuration == configuration

    def test_dump__should_dump_minimal(self) -> None:
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ClassedDummyPlugin
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

    async def test_new_plugin_instance__with_configurable_plugin_with_configuration(
        self,
    ) -> None:
        value = "Hello, world!"
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin, DummyConfiguration(value))
        repository = StaticPluginRepository(
            ConfigurableDummyPluginDefinition, ConfigurableDummyPluginOne.plugin
        )
        instance = await sut.new_plugin_instance(repository, factory=new_target)
        assert isinstance(instance, ConfigurableDummyPluginOne)
        assert instance.configuration.value == value

    async def test_new_plugin_instance__with_configurable_plugin_without_configuration(
        self,
    ) -> None:
        sut = PluginInstanceConfiguration[
            ConfigurableDummyPluginDefinition, ConfigurableDummyPlugin
        ](ConfigurableDummyPluginOne.plugin)
        repository = StaticPluginRepository(
            ConfigurableDummyPluginDefinition, ConfigurableDummyPluginOne.plugin
        )
        instance = await sut.new_plugin_instance(repository, factory=new_target)
        assert isinstance(instance, ConfigurableDummyPluginOne)

    async def test_new_plugin_instance__with_non_configurable_plugin_with_configuration(
        self,
    ) -> None:
        value = "Hello, world!"
        sut = PluginInstanceConfiguration[
            ClassedDummyPluginDefinition, ClassedDummyPlugin
        ](ClassedDummyPluginOne.plugin, DummyConfiguration(value))
        repository = StaticPluginRepository(
            ClassedDummyPluginDefinition, ClassedDummyPluginOne.plugin
        )
        with pytest.raises(HumanFacingException):
            await sut.new_plugin_instance(repository, factory=new_target)

    async def test_new_plugin_instance__with_non_configurable_plugin_without_configuration(
        self,
    ) -> None:
        sut = PluginInstanceConfiguration[
            ClassedDummyPluginDefinition, ClassedDummyPlugin
        ](ClassedDummyPluginOne.plugin.id)
        repository = StaticPluginRepository(
            ClassedDummyPluginDefinition, ClassedDummyPluginOne.plugin
        )
        instance = await sut.new_plugin_instance(repository, factory=new_target)
        assert isinstance(instance, ClassedDummyPluginOne)


class TestPluginInstanceConfigurationMapping(
    ConfigurationMappingTestBase[
        MachineName,
        PluginInstanceConfiguration[ClassedDummyPluginDefinition, ClassedDummyPlugin],
    ]
):
    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return (
            DUMMY_PLUGIN_ONE.id,
            DUMMY_PLUGIN_TWO.id,
            DUMMY_PLUGIN_THREE.id,
            DUMMY_PLUGIN_FOUR.id,
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PluginInstanceConfiguration[ClassedDummyPluginDefinition, ClassedDummyPlugin],
        MachineName,
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
        PluginInstanceConfiguration[ClassedDummyPluginDefinition, ClassedDummyPlugin]
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
        def _load_key(self, item_dump: Dump, key_dump: str, /) -> Dump:
            return {"value": key_dump}

        @override
        def _load_item(self, dump: Dump, /) -> DummyConfiguration:
            raise NotImplementedError

    def test___contains____with_plugin(self) -> None:
        item = DummyConfiguration(DUMMY_PLUGIN_ONE.id)
        sut = self._Sut([item])
        assert DUMMY_PLUGIN_ONE in sut

    def test___contains____with_plugin_id(self) -> None:
        item = DummyConfiguration(DUMMY_PLUGIN_ONE.id)
        sut = self._Sut([item])
        assert DUMMY_PLUGIN_ONE.id in sut

    def test___getitem____with_plugin(self) -> None:
        item = DummyConfiguration(DUMMY_PLUGIN_ONE.id)
        sut = self._Sut([item])
        assert sut[DUMMY_PLUGIN_ONE] is item

    def test___getitem____with_plugin_id(self) -> None:
        item = DummyConfiguration(DUMMY_PLUGIN_ONE.id)
        sut = self._Sut([item])
        assert sut[DUMMY_PLUGIN_ONE.id] is item


class TestPluginInstanceConfigurationSequence(
    ConfigurationSequenceTestBase[
        PluginInstanceConfiguration[ClassedDummyPluginDefinition, ClassedDummyPlugin]
    ]
):
    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PluginInstanceConfiguration[ClassedDummyPluginDefinition, ClassedDummyPlugin],
        int,
    ]:
        return PluginInstanceConfigurationSequence

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PluginInstanceConfiguration[ClassedDummyPluginDefinition, ClassedDummyPlugin]
    ]:
        return (
            PluginInstanceConfiguration("my-first-plugin"),
            PluginInstanceConfiguration("my-second-plugin"),
            PluginInstanceConfiguration("my-third-plugin"),
            PluginInstanceConfiguration("my-fourth-plugin"),
        )
