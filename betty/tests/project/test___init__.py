from __future__ import annotations

from typing import Any, Iterable, TYPE_CHECKING, Self

import pytest
from typing_extensions import override

from betty.assertion import (
    RequiredField,
    assert_bool,
    assert_record,
    assert_setattr,
    assert_int,
)
from betty.assertion.error import AssertionFailed
from betty.config import Configuration
from betty.event_dispatcher import Event, EventHandlerRegistry
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import Entity, UserFacingEntity
from betty.model.ancestry import Ancestry
from betty.plugin.static import StaticPluginRepository
from betty.project import (
    ExtensionConfiguration,
    ExtensionConfigurationMapping,
    ProjectConfiguration,
    LocaleConfiguration,
    LocaleConfigurationSequence,
    EntityReference,
    EntityReferenceSequence,
    EntityTypeConfiguration,
    EntityTypeConfigurationMapping,
    Project,
    ProjectEvent,
)
from betty.project.extension import (
    Extension,
    ConfigurableExtension,
    CyclicDependencyError,
)
from betty.project.factory import ProjectDependentFactory
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.config.collections.sequence import ConfigurationSequenceTestBase
from betty.test_utils.model import DummyEntity
from betty.test_utils.assertion.error import raises_error
from betty.test_utils.project.extension import DummyExtension
from betty.typing import Void

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from betty.machine_name import MachineName
    from pathlib import Path
    from betty.app import App
    from betty.serde.dump import Dump, VoidableDump


class _DummyNonConfigurableExtension(DummyExtension):
    pass


class EntityReferenceTestEntityOne(DummyEntity):
    pass


class EntityReferenceTestEntityTwo(DummyEntity):
    pass


class TestEntityReference:
    async def test_entity_type_with_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne](
            entity_type, None, entity_type_is_constrained=True
        )
        assert entity_type == sut.entity_type
        with pytest.raises(AttributeError):
            sut.entity_type = entity_type

    async def test_entity_type_without_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        sut = EntityReference[EntityReferenceTestEntityOne]()
        assert sut.entity_type is None
        sut.entity_type = entity_type
        assert entity_type == sut.entity_type

    async def test_entity_id(self) -> None:
        entity_id = "123"
        sut = EntityReference[EntityReferenceTestEntityOne]()
        assert sut.entity_id is None
        sut.entity_id = entity_id
        assert entity_id == sut.entity_id

    async def test_load_with_constraint(self) -> None:
        sut = EntityReference(
            EntityReferenceTestEntityOne, entity_type_is_constrained=True
        )
        entity_id = "123"
        dump = entity_id
        sut.load(dump)
        assert entity_id == sut.entity_id

    @pytest.mark.parametrize(
        "dump",
        [
            {
                "entity_type": EntityReferenceTestEntityOne,
                "entity_id": "123",
            },
            {
                "entity_type": EntityReferenceTestEntityTwo,
                "entity_id": "123",
            },
            False,
            123,
        ],
    )
    async def test_load_with_constraint_without_string_should_error(
        self, dump: Dump
    ) -> None:
        sut = EntityReference(
            EntityReferenceTestEntityOne, entity_type_is_constrained=True
        )
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityReferenceTestEntityOne),
        )
        entity_type = EntityReferenceTestEntityOne
        entity_id = "123"
        dump: Dump = {
            "entity_type": entity_type.plugin_id(),
            "entity_id": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        sut.load(dump)
        assert entity_type == sut.entity_type
        assert entity_id == sut.entity_id

    async def test_load_without_constraint_without_entity_type_should_error(
        self,
    ) -> None:
        sut = EntityReference[EntityReferenceTestEntityOne]()
        entity_id = "123"
        dump: Dump = {
            "entity_id": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint_without_string_entity_type_should_error(
        self,
    ) -> None:
        entity_id = "123"
        dump: Dump = {
            "entity_type": None,
            "entity_id": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint_without_importable_entity_type_should_error(
        self,
    ) -> None:
        entity_id = "123"
        dump: Dump = {
            "entity_type": "betty.non_existent.Entity",
            "entity_id": entity_id,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_without_constraint_without_string_entity_id_should_error(
        self,
    ) -> None:
        entity_type = EntityReferenceTestEntityOne
        dump: Dump = {
            "entity_type": entity_type.plugin_id(),
            "entity_id": None,
        }
        sut = EntityReference[EntityReferenceTestEntityOne]()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_dump_with_constraint(self) -> None:
        sut = EntityReference[Entity](Entity, None, entity_type_is_constrained=True)
        entity_id = "123"
        sut.entity_id = entity_id
        expected = entity_id
        assert expected == sut.dump()

    async def test_dump_without_constraint(self) -> None:
        sut = EntityReference[EntityReferenceTestEntityOne]()
        entity_type = EntityReferenceTestEntityOne
        entity_id = "123"
        sut.entity_type = entity_type
        sut.entity_id = entity_id
        expected = {
            "entity_type": entity_type.plugin_id(),
            "entity_id": entity_id,
        }
        assert expected == sut.dump()


class EntityReferenceSequenceTestEntity(DummyEntity):
    pass


class TestEntityReferenceSequence(
    ConfigurationSequenceTestBase[EntityReference[Entity]]
):
    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityReferenceSequenceTestEntity),
        )

    def get_sut(
        self, configurations: Iterable[EntityReference[Entity]] | None = None
    ) -> EntityReferenceSequence[Entity]:
        return EntityReferenceSequence(configurations)

    def get_configurations(
        self,
    ) -> tuple[
        EntityReference[Entity],
        EntityReference[Entity],
        EntityReference[Entity],
        EntityReference[Entity],
    ]:
        return (
            EntityReference[Entity](),
            EntityReference[Entity](EntityReferenceSequenceTestEntity),
            EntityReference[Entity](EntityReferenceSequenceTestEntity, "123"),
            EntityReference[Entity](
                EntityReferenceSequenceTestEntity,
                "123",
                entity_type_is_constrained=True,
            ),
        )


class TestLocaleConfiguration:
    async def test_locale(self) -> None:
        locale = "nl-NL"
        sut = LocaleConfiguration(locale)
        assert locale == sut.locale

    async def test_alias_implicit(self) -> None:
        locale = "nl-NL"
        sut = LocaleConfiguration(locale)
        assert locale == sut.alias

    async def test_alias_explicit(self) -> None:
        locale = "nl-NL"
        alias = "nl"
        sut = LocaleConfiguration(
            locale,
            alias=alias,
        )
        assert alias == sut.alias

    async def test_invalid_alias(self) -> None:
        locale = "nl-NL"
        alias = "/"
        with pytest.raises(AssertionFailed):
            LocaleConfiguration(
                locale,
                alias=alias,
            )

    @pytest.mark.parametrize(
        ("expected", "sut", "other"),
        [
            (
                False,
                LocaleConfiguration(
                    "nl",
                    alias="NL",
                ),
                "not a locale configuration",
            ),
            (
                False,
                LocaleConfiguration(
                    "nl",
                    alias="NL",
                ),
                999,
            ),
            (
                False,
                LocaleConfiguration(
                    "nl",
                    alias="NL",
                ),
                object(),
            ),
        ],
    )
    async def test___eq__(
        self, expected: bool, sut: LocaleConfiguration, other: Any
    ) -> None:
        assert expected == (sut == other)

    async def test_load_with_invalid_dump(self) -> None:
        dump: Dump = {}
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_with_locale(self) -> None:
        dump: Dump = {
            "locale": UNDETERMINED_LOCALE,
        }
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        sut.load(dump)
        assert sut.locale == UNDETERMINED_LOCALE

    async def test_load_with_alias(self) -> None:
        dump: Dump = {
            "locale": UNDETERMINED_LOCALE,
            "alias": "UNDETERMINED_LOCALE",
        }
        sut = LocaleConfiguration(DEFAULT_LOCALE)
        sut.load(dump)
        assert sut.alias == "UNDETERMINED_LOCALE"


class TestLocaleConfigurationSequence(
    ConfigurationSequenceTestBase[LocaleConfiguration]
):
    def get_sut(
        self, configurations: Iterable[Configuration] | None = None
    ) -> LocaleConfigurationSequence:
        return LocaleConfigurationSequence(configurations)  # type: ignore[arg-type]

    def get_configurations(
        self,
    ) -> tuple[
        LocaleConfiguration,
        LocaleConfiguration,
        LocaleConfiguration,
        LocaleConfiguration,
    ]:
        return (
            LocaleConfiguration("en"),
            LocaleConfiguration("nl"),
            LocaleConfiguration("uk"),
            LocaleConfiguration("fr"),
        )

    async def test_update(self) -> None:
        sut = LocaleConfigurationSequence()
        configurations = self.get_configurations()
        other = LocaleConfigurationSequence(configurations)
        sut.update(other)
        assert list(sut) == list(other)

    @override
    async def test___getitem__(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([configurations[0], configurations[1]])
        assert sut[0] == configurations[0]

    @override
    async def test___delitem__(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([configurations[0], configurations[1]])
        del sut[0]
        assert sut[0] == configurations[1]

    async def test___delitem___with_locale(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([configurations[0], configurations[1]])
        del sut[configurations[0].locale]
        with pytest.raises(KeyError):
            sut[configurations[0].locale]

    async def test___delitem___with_one_remaining_locale_configuration(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        sut = LocaleConfigurationSequence(
            [
                locale_configuration_a,
            ]
        )
        del sut["nl-NL"]
        assert len(sut) == 1
        sut[DEFAULT_LOCALE]

    async def test_default_without_explicit_locale_configurations(self) -> None:
        sut = LocaleConfigurationSequence()
        assert LocaleConfiguration("en-US") == sut.default

    async def test_default_without_explicit_default(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        locale_configuration_b = LocaleConfiguration("en-US")
        sut = LocaleConfigurationSequence(
            [
                locale_configuration_a,
                locale_configuration_b,
            ]
        )
        assert locale_configuration_a == sut.default

    @override
    async def test_replace_without_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 1
        self.get_configurations()
        sut.replace()
        assert len(sut) == 1

    @override
    async def test_replace_with_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 1
        configurations = self.get_configurations()
        sut.replace(*configurations)
        assert len(sut) == len(configurations)


class _DummyConfigurableExtensionConfiguration(Configuration):
    def __init__(self):
        super().__init__()
        self.check = False

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, _DummyConfigurableExtensionConfiguration):
            return NotImplemented
        return self.check == other.check

    @override
    def update(self, other: Self) -> None:
        pass

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("check", assert_bool() | assert_setattr(self, "check"))
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return {
            "check": self.check,
        }


class _DummyConfigurableExtension(
    DummyExtension, ConfigurableExtension[_DummyConfigurableExtensionConfiguration]
):
    @classmethod
    def default_configuration(cls) -> _DummyConfigurableExtensionConfiguration:
        return _DummyConfigurableExtensionConfiguration()


class _DummyConfiguration(Configuration):
    @override
    def update(self, other: Self) -> None:
        pass

    @override
    def load(self, dump: Dump) -> None:
        pass

    @override
    def dump(self) -> VoidableDump:
        return Void


class TestExtensionConfiguration:
    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(DummyExtension, _DummyConfigurableExtension),
        )

    async def test_extension_type(self) -> None:
        extension_type = DummyExtension
        sut = ExtensionConfiguration(extension_type)
        assert extension_type == sut.extension_type

    async def test_enabled(self) -> None:
        enabled = True
        sut = ExtensionConfiguration(
            DummyExtension,
            enabled=enabled,
        )
        assert enabled == sut.enabled
        sut.enabled = False

    async def test_configuration(self) -> None:
        extension_type_configuration = _DummyConfiguration()
        sut = ExtensionConfiguration(
            _DummyConfigurableExtension,
            extension_configuration=extension_type_configuration,
        )
        assert extension_type_configuration == sut.extension_configuration

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (
                True,
                ExtensionConfiguration(DummyExtension),
                ExtensionConfiguration(DummyExtension),
            ),
            (
                False,
                ExtensionConfiguration(
                    DummyExtension,
                    extension_configuration=_DummyConfiguration(),
                ),
                ExtensionConfiguration(
                    DummyExtension,
                    extension_configuration=_DummyConfiguration(),
                ),
            ),
            (
                False,
                ExtensionConfiguration(DummyExtension),
                ExtensionConfiguration(
                    DummyExtension,
                    enabled=False,
                ),
            ),
            (
                False,
                ExtensionConfiguration(DummyExtension),
                ExtensionConfiguration(_DummyConfigurableExtension),
            ),
        ],
    )
    async def test___eq__(
        self, expected: bool, one: ExtensionConfiguration, other: ExtensionConfiguration
    ) -> None:
        assert expected == (one == other)

    async def test_load_without_extension(self) -> None:
        with raises_error(error_type=AssertionFailed):
            ExtensionConfiguration(DummyExtension).load({})

    async def test_load_with_extension(self) -> None:
        sut = ExtensionConfiguration(DummyExtension)
        sut.load({"extension": _DummyConfigurableExtension.plugin_id()})
        assert sut.extension_type == _DummyConfigurableExtension
        assert sut.enabled

    async def test_load_with_enabled(self) -> None:
        sut = ExtensionConfiguration(DummyExtension)
        sut.load(
            {"extension": _DummyConfigurableExtension.plugin_id(), "enabled": False}
        )
        assert not sut.enabled

    async def test_load_with_configuration(self) -> None:
        sut = ExtensionConfiguration(_DummyConfigurableExtension)
        sut.load(
            {
                "extension": _DummyConfigurableExtension.plugin_id(),
                "configuration": {
                    "check": True,
                },
            }
        )
        extension_configuration = sut.extension_configuration
        assert isinstance(
            extension_configuration, _DummyConfigurableExtensionConfiguration
        )
        assert extension_configuration.check


class ExtensionTypeConfigurationMappingTestExtension0(DummyExtension):
    pass


class ExtensionTypeConfigurationMappingTestExtension1(DummyExtension):
    pass


class ExtensionTypeConfigurationMappingTestExtension2(DummyExtension):
    pass


class ExtensionTypeConfigurationMappingTestExtension3(DummyExtension):
    pass


class TestExtensionConfigurationMapping(
    ConfigurationMappingTestBase[type[Extension], ExtensionConfiguration]
):
    def get_configuration_keys(
        self,
    ) -> tuple[type[Extension], type[Extension], type[Extension], type[Extension]]:
        return (
            ExtensionTypeConfigurationMappingTestExtension0,
            ExtensionTypeConfigurationMappingTestExtension1,
            ExtensionTypeConfigurationMappingTestExtension2,
            ExtensionTypeConfigurationMappingTestExtension3,
        )

    def get_sut(
        self, configurations: Iterable[ExtensionConfiguration] | None = None
    ) -> ExtensionConfigurationMapping:
        return ExtensionConfigurationMapping(configurations)

    def get_configurations(
        self,
    ) -> tuple[
        ExtensionConfiguration,
        ExtensionConfiguration,
        ExtensionConfiguration,
        ExtensionConfiguration,
    ]:
        return (
            ExtensionConfiguration(self.get_configuration_keys()[0]),
            ExtensionConfiguration(self.get_configuration_keys()[1]),
            ExtensionConfiguration(self.get_configuration_keys()[2], enabled=False),
            ExtensionConfiguration(self.get_configuration_keys()[3], enabled=False),
        )

    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(*self.get_configuration_keys()),
        )


class EntityTypeConfigurationTestEntityOne(UserFacingEntity, DummyEntity):
    pass


class EntityTypeConfigurationTestEntityOther(UserFacingEntity, DummyEntity):
    pass


class TestEntityTypeConfiguration:
    async def test_entity_type(self) -> None:
        entity_type = EntityTypeConfigurationTestEntityOne
        sut = EntityTypeConfiguration(entity_type)
        assert entity_type == sut.entity_type

    @pytest.mark.parametrize(
        "generate_html_list,",
        [
            True,
            False,
        ],
    )
    async def test_generate_html_list(self, generate_html_list: bool) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        sut.generate_html_list = generate_html_list
        assert generate_html_list == sut.generate_html_list

    async def test_load_with_empty_configuration(self) -> None:
        dump: Dump = {}
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_with_minimal_configuration(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityTypeConfigurationTestEntityOne),
        )
        dump: Dump = {
            "entity_type": EntityTypeConfigurationTestEntityOne.plugin_id(),
        }
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        sut.load(dump)

    @pytest.mark.parametrize(
        "generate_html_list,",
        [
            True,
            False,
        ],
    )
    async def test_load_with_generate_html_list(
        self, generate_html_list: bool, mocker: MockerFixture
    ) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(EntityTypeConfigurationTestEntityOne),
        )
        dump: Dump = {
            "entity_type": EntityTypeConfigurationTestEntityOne.plugin_id(),
            "generate_html_list": generate_html_list,
        }
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        sut.load(dump)
        assert generate_html_list == sut.generate_html_list

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        expected = {
            "entity_type": EntityTypeConfigurationTestEntityOne.plugin_id(),
        }
        assert expected == sut.dump()

    async def test_dump_with_generate_html_list(self) -> None:
        sut = EntityTypeConfiguration(
            entity_type=EntityTypeConfigurationTestEntityOne,
            generate_html_list=False,
        )
        expected = {
            "entity_type": EntityTypeConfigurationTestEntityOne.plugin_id(),
            "generate_html_list": False,
        }
        assert expected == sut.dump()

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (
                True,
                EntityTypeConfiguration(
                    entity_type=EntityTypeConfigurationTestEntityOne,
                    generate_html_list=True,
                ),
                EntityTypeConfiguration(
                    entity_type=EntityTypeConfigurationTestEntityOne,
                    generate_html_list=True,
                ),
            ),
            (
                False,
                EntityTypeConfiguration(
                    entity_type=EntityTypeConfigurationTestEntityOne,
                    generate_html_list=True,
                ),
                EntityTypeConfiguration(
                    entity_type=EntityTypeConfigurationTestEntityOne,
                    generate_html_list=False,
                ),
            ),
            (
                False,
                EntityTypeConfiguration(
                    entity_type=EntityTypeConfigurationTestEntityOne,
                    generate_html_list=True,
                ),
                EntityTypeConfiguration(
                    entity_type=EntityTypeConfigurationTestEntityOther,
                    generate_html_list=True,
                ),
            ),
        ],
    )
    async def test___eq__(
        self,
        expected: bool,
        one: EntityTypeConfiguration,
        other: EntityTypeConfiguration,
    ) -> None:
        assert expected == (one == other)


class EntityTypeConfigurationMappingTestEntity0(DummyEntity):
    pass


class EntityTypeConfigurationMappingTestEntity1(DummyEntity):
    pass


class EntityTypeConfigurationMappingTestEntity2(DummyEntity):
    pass


class EntityTypeConfigurationMappingTestEntity3(DummyEntity):
    pass


class TestEntityTypeConfigurationMapping(
    ConfigurationMappingTestBase[type[Entity], EntityTypeConfiguration]
):
    @pytest.fixture(autouse=True)
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY",
            new=StaticPluginRepository(
                EntityTypeConfigurationMappingTestEntity0,
                EntityTypeConfigurationMappingTestEntity1,
                EntityTypeConfigurationMappingTestEntity2,
                EntityTypeConfigurationMappingTestEntity3,
            ),
        )

    def get_configuration_keys(
        self,
    ) -> tuple[type[Entity], type[Entity], type[Entity], type[Entity]]:
        return (
            EntityTypeConfigurationMappingTestEntity0,
            EntityTypeConfigurationMappingTestEntity1,
            EntityTypeConfigurationMappingTestEntity2,
            EntityTypeConfigurationMappingTestEntity3,
        )

    def get_sut(
        self, configurations: Iterable[EntityTypeConfiguration] | None = None
    ) -> EntityTypeConfigurationMapping:
        return EntityTypeConfigurationMapping(configurations)

    def get_configurations(
        self,
    ) -> tuple[
        EntityTypeConfiguration,
        EntityTypeConfiguration,
        EntityTypeConfiguration,
        EntityTypeConfiguration,
    ]:
        return (
            EntityTypeConfiguration(self.get_configuration_keys()[0]),
            EntityTypeConfiguration(self.get_configuration_keys()[1]),
            EntityTypeConfiguration(self.get_configuration_keys()[2]),
            EntityTypeConfiguration(self.get_configuration_keys()[3]),
        )


class TestProjectConfiguration:
    async def test_configuration_file_path(self, tmp_path: Path) -> None:
        old_configuration_file_path = tmp_path / "betty.json"
        sut = ProjectConfiguration(old_configuration_file_path)
        assert sut.configuration_file_path == old_configuration_file_path
        new_configuration_file_path = tmp_path / "betty.yaml"
        sut.configuration_file_path = new_configuration_file_path
        assert sut.configuration_file_path == new_configuration_file_path

    async def test_name(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        name = "MyFirstBettySite"
        sut.name = name
        assert sut.name == name

    async def test_url(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        url = "https://example.com/example"
        sut.url = url
        assert sut.url == url

    async def test_url_without_scheme_should_error(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with pytest.raises(AssertionFailed):
            sut.url = "/"

    async def test_url_without_path_should_error(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with pytest.raises(AssertionFailed):
            sut.url = "file://"

    async def test_base_url(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        url = "https://example.com/example"
        sut.url = url
        assert sut.base_url == "https://example.com"

    async def test_root_path(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        url = "https://example.com/example"
        sut.url = url
        assert sut.root_path == "/example"

    async def test_clean_urls(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        clean_urls = True
        sut.clean_urls = clean_urls
        assert clean_urls == sut.clean_urls

    async def test_author_without_author(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        assert not sut.author

    async def test_author_with_author(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        author = "Bart"
        sut.author = author
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test_load_should_load_minimal(self, tmp_path: Path) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert dump["url"] == sut.url
        assert sut.title.localize(DEFAULT_LOCALIZER) == "Betty"
        assert not sut.author
        assert not sut.debug
        assert not sut.clean_urls

    async def test_load_should_load_name(self, tmp_path: Path) -> None:
        name = "MyFirstBettySite"
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["name"] = name
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.name == name

    async def test_load_should_load_title(self, tmp_path: Path) -> None:
        title = "My first Betty site"
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["title"] = title
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.title.localize(DEFAULT_LOCALIZER) == title

    async def test_load_should_load_author(self, tmp_path: Path) -> None:
        author = "Bart"
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["author"] = author
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test_load_should_load_locale_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        dump = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["locales"] = [{"locale": locale}]
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.locales == LocaleConfigurationSequence([LocaleConfiguration(locale)])

    async def test_load_should_load_locale_alias(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        alias = "nl"
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["locales"] = [{"locale": locale, "alias": alias}]
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.locales == LocaleConfigurationSequence(
            [
                LocaleConfiguration(
                    locale,
                    alias=alias,
                ),
            ]
        )

    async def test_load_should_clean_urls(self, tmp_path: Path) -> None:
        clean_urls = True
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["clean_urls"] = clean_urls
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.clean_urls == clean_urls

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_load_should_load_debug(self, debug: bool, tmp_path: Path) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["debug"] = debug
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.load(dump)
        assert sut.debug == debug

    async def test_load_should_load_one_extension_with_configuration(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(_DummyConfigurableExtension),
        )
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        extension_configuration = {
            "check": False,
        }
        dump["extensions"] = {
            _DummyConfigurableExtension.plugin_id(): {
                "configuration": extension_configuration,
            },
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        expected = ExtensionConfiguration(
            _DummyConfigurableExtension,
            extension_configuration=_DummyConfigurableExtensionConfiguration(),
        )
        sut.load(dump)
        assert sut.extensions[_DummyConfigurableExtension] == expected

    async def test_load_should_load_one_extension_without_configuration(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(_DummyNonConfigurableExtension),
        )
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["extensions"] = {
            _DummyNonConfigurableExtension.plugin_id(): {},
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        expected = ExtensionConfiguration(_DummyNonConfigurableExtension)
        sut.load(dump)
        assert sut.extensions[_DummyNonConfigurableExtension] == expected

    async def test_load_extension_with_invalid_configuration_should_raise_error(
        self, tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["extensions"] = {
            _DummyConfigurableExtension.plugin_id(): 1337,
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_unknown_extension_type_name_should_error(
        self, tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["extensions"] = {
            "non.existent.type": {},
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_not_an_extension_type_name_should_error(
        self, tmp_path: Path
    ) -> None:
        dump: Any = ProjectConfiguration(tmp_path / "betty.json").dump()
        dump["extensions"] = {
            "%s.%s" % (self.__class__.__module__, self.__class__.__name__): {},
        }
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_should_error_if_invalid_config(self, tmp_path: Path) -> None:
        dump: Dump = {}
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_dump_should_dump_minimal(self, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        dump: Any = sut.dump()
        assert dump["url"] == sut.url
        assert sut.title.localize(DEFAULT_LOCALIZER) == "Betty"
        assert not sut.author
        assert not sut.debug
        assert sut.root_path == ""
        assert not sut.clean_urls

    async def test_dump_should_dump_title(self, tmp_path: Path) -> None:
        title = "My first Betty site"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.title = title
        dump: Any = sut.dump()
        assert title == dump["title"]

    async def test_dump_should_dump_name(self, tmp_path: Path) -> None:
        name = "MyFirstBettySite"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.name = name
        dump: Any = sut.dump()
        assert dump["name"] == name

    async def test_dump_should_dump_author(self, tmp_path: Path) -> None:
        author = "Bart"
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.author = author
        dump: Any = sut.dump()
        assert author == dump["author"]

    async def test_dump_should_dump_locale_locale(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        locale_configuration = LocaleConfiguration(locale)
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.locales.replace(locale_configuration)
        dump: Any = sut.dump()
        assert dump["locales"] == [
            {"locale": locale},
        ]

    async def test_dump_should_dump_locale_alias(self, tmp_path: Path) -> None:
        locale = "nl-NL"
        alias = "nl"
        locale_configuration = LocaleConfiguration(
            locale,
            alias=alias,
        )
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.locales.replace(locale_configuration)
        dump: Any = sut.dump()
        assert dump["locales"] == [
            {"locale": locale, "alias": alias},
        ]

    async def test_dump_should_dump_clean_urls(self, tmp_path: Path) -> None:
        clean_urls = True
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.clean_urls = clean_urls
        dump: Any = sut.dump()
        assert clean_urls == dump["clean_urls"]

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_dump_should_dump_debug(self, debug: bool, tmp_path: Path) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.debug = debug
        dump: Any = sut.dump()
        assert debug == dump["debug"]

    async def test_dump_should_dump_one_extension_with_configuration(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.extensions.append(
            ExtensionConfiguration(
                _DummyConfigurableExtension,
                extension_configuration=_DummyConfigurableExtensionConfiguration(),
            )
        )
        dump: Any = sut.dump()
        expected = {
            "enabled": True,
            "configuration": {
                "check": False,
            },
        }
        assert expected == dump["extensions"][_DummyConfigurableExtension.plugin_id()]

    async def test_dump_should_dump_one_extension_without_configuration(
        self, tmp_path: Path
    ) -> None:
        sut = ProjectConfiguration(tmp_path / "betty.json")
        sut.extensions.append(ExtensionConfiguration(_DummyNonConfigurableExtension))
        dump: Any = sut.dump()
        expected = {
            "enabled": True,
        }
        assert (
            expected == dump["extensions"][_DummyNonConfigurableExtension.plugin_id()]
        )

    async def test_dump_should_error_if_invalid_config(self, tmp_path: Path) -> None:
        dump: Dump = {}
        sut = ProjectConfiguration(tmp_path / "betty.json")
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)


class _TrackerEvent(Event):
    def __init__(self, carrier: list[_TrackableExtension]):
        self.carrier = carrier


class _TrackableExtension(DummyExtension):
    def register_event_handlers(self, registry: EventHandlerRegistry) -> None:
        registry.add_handler(_TrackerEvent, self._track)

    async def _track(self, event: _TrackerEvent) -> None:
        event.carrier.append(self)


class _NonConfigurableExtension(_TrackableExtension):
    pass


class _ConfigurableExtensionConfiguration(Configuration):
    def __init__(self, check: int = 0):
        super().__init__()
        self.check = check

    @override
    def update(self, other: Self) -> None:
        self.check = other.check

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("check", assert_int() | assert_setattr(self, "check"))
        )(dump)

    @override
    def dump(self) -> VoidableDump:
        return {"check": self.check}


class _CyclicDependencyOneExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[MachineName]:
        return {_CyclicDependencyTwoExtension.plugin_id()}


class _CyclicDependencyTwoExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[MachineName]:
        return {_CyclicDependencyOneExtension.plugin_id()}


class _DependsOnNonConfigurableExtensionExtension(_TrackableExtension):
    @classmethod
    def depends_on(cls) -> set[MachineName]:
        return {_NonConfigurableExtension.plugin_id()}


class _AlsoDependsOnNonConfigurableExtensionExtension(_TrackableExtension):
    @classmethod
    def depends_on(cls) -> set[MachineName]:
        return {_NonConfigurableExtension.plugin_id()}


class _DependsOnNonConfigurableExtensionExtensionExtension(_TrackableExtension):
    @classmethod
    def depends_on(cls) -> set[MachineName]:
        return {_DependsOnNonConfigurableExtensionExtension.plugin_id()}


class _ComesBeforeNonConfigurableExtensionExtension(_TrackableExtension):
    @classmethod
    def comes_before(cls) -> set[MachineName]:
        return {_NonConfigurableExtension.plugin_id()}


class _ComesAfterNonConfigurableExtensionExtension(_TrackableExtension):
    @classmethod
    def comes_after(cls) -> set[MachineName]:
        return {_NonConfigurableExtension.plugin_id()}


class _ConfigurableExtension(
    ConfigurableExtension[_ConfigurableExtensionConfiguration], DummyExtension
):
    @classmethod
    def default_configuration(cls) -> _ConfigurableExtensionConfiguration:
        return _ConfigurableExtensionConfiguration(False)


class TestProject:
    @pytest.fixture()
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(
                _NonConfigurableExtension,
                _ConfigurableExtension,
                _DependsOnNonConfigurableExtensionExtension,
                _DependsOnNonConfigurableExtensionExtensionExtension,
                _CyclicDependencyOneExtension,
                _CyclicDependencyTwoExtension,
            ),
        )

    @pytest.mark.usefixtures("_extensions")
    async def test_bootstrap(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.append(
                ExtensionConfiguration(_NonConfigurableExtension)
            )
            async with sut:
                extension = sut.extensions[_NonConfigurableExtension.plugin_id()]
                assert extension._bootstrapped

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_one_extension(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.append(
                ExtensionConfiguration(_NonConfigurableExtension)
            )
            async with sut:
                extension = sut.extensions[_NonConfigurableExtension.plugin_id()]
                assert isinstance(extension, _NonConfigurableExtension)

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_one_configurable_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            check = 1337
            sut.configuration.extensions.append(
                ExtensionConfiguration(
                    _ConfigurableExtension,
                    extension_configuration=_ConfigurableExtensionConfiguration(
                        check=check,
                    ),
                )
            )
            async with sut:
                extension = sut.extensions[_ConfigurableExtension.plugin_id()]
                assert isinstance(extension, _ConfigurableExtension)
                assert check == extension.configuration.check

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_one_extension_with_single_chained_dependency(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.append(
                ExtensionConfiguration(
                    _DependsOnNonConfigurableExtensionExtensionExtension
                )
            )
            async with sut:
                carrier: list[_TrackableExtension] = []
                await sut.event_dispatcher.dispatch(_TrackerEvent(carrier))
                assert len(carrier) == 3
                assert isinstance(carrier[0], _NonConfigurableExtension)
                assert isinstance(
                    carrier[1], _DependsOnNonConfigurableExtensionExtension
                )
                assert isinstance(
                    carrier[2], _DependsOnNonConfigurableExtensionExtensionExtension
                )

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.append(
                ExtensionConfiguration(_DependsOnNonConfigurableExtensionExtension)
            )
            sut.configuration.extensions.append(
                ExtensionConfiguration(_AlsoDependsOnNonConfigurableExtensionExtension)
            )
            async with sut:
                carrier: list[_TrackableExtension] = []
                await sut.event_dispatcher.dispatch(_TrackerEvent(carrier))
                assert len(carrier) == 3
                assert isinstance(carrier[0], _NonConfigurableExtension)
                assert _DependsOnNonConfigurableExtensionExtension in [
                    type(extension) for extension in carrier
                ]
                assert _AlsoDependsOnNonConfigurableExtensionExtension in [
                    type(extension) for extension in carrier
                ]

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_multiple_extensions_with_cyclic_dependencies(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.append(
                ExtensionConfiguration(_CyclicDependencyOneExtension)
            )
            with pytest.raises(CyclicDependencyError):  # noqa PT012
                async with sut:
                    pass

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_comes_before_with_other_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.append(
                ExtensionConfiguration(_NonConfigurableExtension)
            )
            sut.configuration.extensions.append(
                ExtensionConfiguration(_ComesBeforeNonConfigurableExtensionExtension)
            )
            async with sut:
                carrier: list[_TrackableExtension] = []
                await sut.event_dispatcher.dispatch(_TrackerEvent(carrier))
                assert len(carrier) == 2
                assert isinstance(
                    carrier[0], _ComesBeforeNonConfigurableExtensionExtension
                )
                assert isinstance(carrier[1], _NonConfigurableExtension)

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_comes_before_without_other_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.append(
                ExtensionConfiguration(_ComesBeforeNonConfigurableExtensionExtension)
            )
            async with sut:
                carrier: list[_TrackableExtension] = []
                await sut.event_dispatcher.dispatch(_TrackerEvent(carrier))
                assert len(carrier) == 1
                assert isinstance(
                    carrier[0], _ComesBeforeNonConfigurableExtensionExtension
                )

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_comes_after_with_other_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.append(
                ExtensionConfiguration(_ComesAfterNonConfigurableExtensionExtension)
            )
            sut.configuration.extensions.append(
                ExtensionConfiguration(_NonConfigurableExtension)
            )
            async with sut:
                carrier: list[_TrackableExtension] = []
                await sut.event_dispatcher.dispatch(_TrackerEvent(carrier))
                assert len(carrier) == 2
                assert isinstance(carrier[0], _NonConfigurableExtension)
                assert isinstance(
                    carrier[1], _ComesAfterNonConfigurableExtensionExtension
                )

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_comes_after_without_other_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.append(
                ExtensionConfiguration(_ComesAfterNonConfigurableExtensionExtension)
            )
            async with sut:
                carrier: list[_TrackableExtension] = []
                await sut.event_dispatcher.dispatch(_TrackerEvent(carrier))
                assert len(carrier) == 1
                assert isinstance(
                    carrier[0], _ComesAfterNonConfigurableExtensionExtension
                )

    async def test_ancestry_with___init___ancestry(
        self, new_temporary_app: App
    ) -> None:
        ancestry = Ancestry()
        async with Project.new_temporary(
            new_temporary_app, ancestry=ancestry
        ) as sut, sut:
            assert sut.ancestry is ancestry

    async def test_ancestry_without___init___ancestry(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.ancestry  # noqa B018

    async def test_app(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assert sut.app is new_temporary_app

    async def test_assets(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assert len(sut.assets.assets_directory_paths) > 0

    async def test_event_dispatcher(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.event_dispatcher  # noqa B018

    async def test_jinja2_environment(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.jinja2_environment  # noqa B018

    async def test_localizers(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assert len(list(sut.localizers.locales)) > 0

    async def test_name_with_configuration_name(self, new_temporary_app: App) -> None:
        name = "hello-world"
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.name = name
            async with sut:
                assert sut.name == name

    async def test_name_without_configuration_name(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.name  # noqa B018

    async def test_renderer(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.renderer  # noqa B018

    async def test_static_url_generator(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.static_url_generator  # noqa B018

    async def test_url_generator(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.url_generator  # noqa B018

    async def test_new_dependent(self, new_temporary_app: App) -> None:
        class Dependent(ProjectDependentFactory):
            def __init__(self, project: Project):
                self.project = project

            @classmethod
            def new_for_project(cls, project: Project) -> Self:
                return cls(project)

        async with Project.new_temporary(new_temporary_app) as sut, sut:
            dependent = sut.new_dependent(Dependent)
            assert dependent.project is sut


class TestProjectEvent:
    async def test_project(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = ProjectEvent(project)
            assert sut.project is project
