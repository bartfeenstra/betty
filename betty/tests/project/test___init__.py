from __future__ import annotations

from typing import Any, Iterable, TYPE_CHECKING, Self

import pytest

from betty.assertion import (
    RequiredField,
    assert_bool,
    assert_record,
    assert_setattr,
    assert_int,
)
from betty.assertion.error import AssertionFailed
from betty.config import Configuration
from betty.locale import DEFAULT_LOCALE, UNDETERMINED_LOCALE
from betty.model import Entity, get_entity_type_name, UserFacingEntity
from betty.model.ancestry import Ancestry
from betty.project import (
    ExtensionConfiguration,
    ExtensionConfigurationMapping,
    ProjectConfiguration,
    LocaleConfiguration,
    LocaleConfigurationMapping,
    EntityReference,
    EntityReferenceSequence,
    EntityTypeConfiguration,
    EntityTypeConfigurationMapping,
    Project,
)
from betty.project.extension import (
    Extension,
    ConfigurableExtension,
    CyclicDependencyError,
)
from betty.tests.assertion import raises_error
from betty.tests.test_config import (
    ConfigurationMappingTestBase,
    ConfigurationSequenceTestBase,
)
from betty.typing import Void

if TYPE_CHECKING:
    from betty.app import App
    from collections.abc import Sequence
    from betty.serde.dump import Dump, VoidableDump


class EntityReferenceTestEntityOne(Entity):
    pass


class EntityReferenceTestEntityTwo(Entity):
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

    async def test_load_without_constraint(self) -> None:
        entity_type = EntityReferenceTestEntityOne
        entity_id = "123"
        dump: Dump = {
            "entity_type": get_entity_type_name(entity_type),
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
            "entity_type": get_entity_type_name(entity_type),
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
            "entity_type": get_entity_type_name(entity_type),
            "entity_id": entity_id,
        }
        assert expected == sut.dump()


class EntityReferenceSequenceTestEntity(Entity):
    pass


class TestEntityReferenceSequence(
    ConfigurationSequenceTestBase[EntityReference[Entity]]
):
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
            EntityReference[Entity](Entity),
            EntityReference[Entity](Entity, "123"),
            EntityReference[Entity](Entity, "123", entity_type_is_constrained=True),
        )

    async def test_load_item(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        dumps = [configuration.dump() for configuration in configurations]
        non_void_dumps: Sequence[Dump] = [
            dump  # type: ignore[misc]
            for dump in dumps
            if dump is not Void
        ]
        assert non_void_dumps, "At least one configuration object must return a configuration dump that is not Void"
        for dump in non_void_dumps:
            sut.load_item(dump)


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


class TestLocaleConfigurationMapping(
    ConfigurationMappingTestBase[str, LocaleConfiguration]
):
    def get_configuration_keys(self) -> tuple[str, str, str, str]:
        return "en", "nl", "uk", "fr"

    def get_sut(
        self, configurations: Iterable[Configuration] | None = None
    ) -> LocaleConfigurationMapping:
        return LocaleConfigurationMapping(configurations)  # type: ignore[arg-type]

    def get_configurations(
        self,
    ) -> tuple[
        LocaleConfiguration,
        LocaleConfiguration,
        LocaleConfiguration,
        LocaleConfiguration,
    ]:
        return (
            LocaleConfiguration(self.get_configuration_keys()[0]),
            LocaleConfiguration(self.get_configuration_keys()[1]),
            LocaleConfiguration(self.get_configuration_keys()[2]),
            LocaleConfiguration(self.get_configuration_keys()[3]),
        )

    async def test_load_item(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        dumps = [configuration.dump() for configuration in configurations]
        non_void_dumps: Sequence[Dump] = [
            dump  # type: ignore[misc]
            for dump in dumps
            if dump is not Void
        ]
        assert non_void_dumps, "At least one configuration object must return a configuration dump that is not Void"
        for dump in non_void_dumps:
            sut.load_item(dump)

    async def test_delitem(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut([configurations[0], configurations[1]])
        del sut[self.get_configuration_keys()[1]]
        assert [configurations[0]] == list(sut.values())

    async def test_delitem_with_one_remaining_locale_configuration(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        sut = LocaleConfigurationMapping(
            [
                locale_configuration_a,
            ]
        )
        del sut["nl-NL"]
        assert len(sut) == 1
        assert DEFAULT_LOCALE in sut

    async def test_default_without_explicit_locale_configurations(self) -> None:
        sut = LocaleConfigurationMapping()
        assert LocaleConfiguration("en-US") == sut.default

    async def test_default_without_explicit_default(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        locale_configuration_b = LocaleConfiguration("en-US")
        sut = LocaleConfigurationMapping(
            [
                locale_configuration_a,
                locale_configuration_b,
            ]
        )
        assert locale_configuration_a == sut.default

    async def test_default_with_explicit_default(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        locale_configuration_b = LocaleConfiguration("en-US")
        sut = LocaleConfigurationMapping(
            [
                locale_configuration_a,
            ]
        )
        sut.default = locale_configuration_b
        assert locale_configuration_b == sut.default

    async def test_replace_without_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 1
        self.get_configurations()
        sut.replace()
        assert len(sut) == 1

    async def test_replace_with_items(self) -> None:
        sut = self.get_sut()
        sut.clear()
        assert len(sut) == 1
        configurations = self.get_configurations()
        sut.replace(*configurations)
        assert len(sut) == len(configurations)


class _DummyExtension(Extension):
    pass


class _DummyConfigurableExtensionConfiguration(Configuration):
    def __init__(self):
        super().__init__()
        self.check = False

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, _DummyConfigurableExtensionConfiguration):
            return NotImplemented
        return self.check == other.check

    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("check", assert_bool() | assert_setattr(self, "check"))
        )(dump)

    def dump(self) -> VoidableDump:
        return {
            "check": self.check,
        }


class _DummyConfigurableExtension(
    ConfigurableExtension[_DummyConfigurableExtensionConfiguration]
):
    @classmethod
    def default_configuration(cls) -> _DummyConfigurableExtensionConfiguration:
        return _DummyConfigurableExtensionConfiguration()


class TestExtensionConfiguration:
    async def test_extension_type(self) -> None:
        extension_type = _DummyExtension
        sut = ExtensionConfiguration(extension_type)
        assert extension_type == sut.extension_type

    async def test_enabled(self) -> None:
        enabled = True
        sut = ExtensionConfiguration(
            _DummyExtension,
            enabled=enabled,
        )
        assert enabled == sut.enabled
        sut.enabled = False

    async def test_configuration(self) -> None:
        extension_type_configuration = Configuration()
        sut = ExtensionConfiguration(
            Extension,
            extension_configuration=extension_type_configuration,
        )
        assert extension_type_configuration == sut.extension_configuration

    @pytest.mark.parametrize(
        ("expected", "one", "other"),
        [
            (
                True,
                ExtensionConfiguration(_DummyExtension),
                ExtensionConfiguration(_DummyExtension),
            ),
            (
                False,
                ExtensionConfiguration(
                    _DummyExtension,
                    extension_configuration=Configuration(),
                ),
                ExtensionConfiguration(
                    _DummyExtension,
                    extension_configuration=Configuration(),
                ),
            ),
            (
                False,
                ExtensionConfiguration(_DummyExtension),
                ExtensionConfiguration(
                    _DummyExtension,
                    enabled=False,
                ),
            ),
            (
                False,
                ExtensionConfiguration(_DummyExtension),
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
            ExtensionConfiguration(_DummyExtension).load({})

    async def test_load_with_extension(self) -> None:
        sut = ExtensionConfiguration(_DummyExtension)
        sut.load({"extension": _DummyConfigurableExtension.name()})
        assert sut.extension_type == _DummyConfigurableExtension
        assert sut.enabled

    async def test_load_with_enabled(self) -> None:
        sut = ExtensionConfiguration(_DummyExtension)
        sut.load({"extension": _DummyConfigurableExtension.name(), "enabled": False})
        assert not sut.enabled

    async def test_load_with_configuration(self) -> None:
        sut = ExtensionConfiguration(_DummyConfigurableExtension)
        sut.load(
            {
                "extension": _DummyConfigurableExtension.name(),
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


class ExtensionTypeConfigurationMappingTestExtension0(Extension):
    pass


class ExtensionTypeConfigurationMappingTestExtension1(Extension):
    pass


class ExtensionTypeConfigurationMappingTestExtension2(Extension):
    pass


class ExtensionTypeConfigurationMappingTestExtension3(Extension):
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

    async def test_load_item(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        dumps = [configuration.dump() for configuration in configurations]
        non_void_dumps: Sequence[Dump] = [
            dump  # type: ignore[misc]
            for dump in dumps
            if dump is not Void
        ]
        assert non_void_dumps, "At least one configuration object must return a configuration dump that is not Void"
        for dump in non_void_dumps:
            sut.load_item(dump)


class EntityTypeConfigurationTestEntityOne(UserFacingEntity, Entity):
    pass


class EntityTypeConfigurationTestEntityOther(UserFacingEntity, Entity):
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

    async def test_load_with_minimal_configuration(self) -> None:
        dump: Dump = {
            "entity_type": get_entity_type_name(EntityTypeConfigurationTestEntityOne),
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
    async def test_load_with_generate_html_list(self, generate_html_list: bool) -> None:
        dump: Dump = {
            "entity_type": get_entity_type_name(EntityTypeConfigurationTestEntityOne),
            "generate_html_list": generate_html_list,
        }
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        sut.load(dump)
        assert generate_html_list == sut.generate_html_list

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = EntityTypeConfiguration(EntityTypeConfigurationTestEntityOne)
        expected = {
            "entity_type": "betty.tests.project.test___init__.EntityTypeConfigurationTestEntityOne",
        }
        assert expected == sut.dump()

    async def test_dump_with_generate_html_list(self) -> None:
        sut = EntityTypeConfiguration(
            entity_type=EntityTypeConfigurationTestEntityOne,
            generate_html_list=False,
        )
        expected = {
            "entity_type": "betty.tests.project.test___init__.EntityTypeConfigurationTestEntityOne",
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


class EntityTypeConfigurationMappingTestEntity0(Entity):
    pass


class EntityTypeConfigurationMappingTestEntity1(Entity):
    pass


class EntityTypeConfigurationMappingTestEntity2(Entity):
    pass


class EntityTypeConfigurationMappingTestEntity3(Entity):
    pass


class TestEntityTypeConfigurationMapping(
    ConfigurationMappingTestBase[type[Entity], EntityTypeConfiguration]
):
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

    async def test_load_item(self) -> None:
        configurations = self.get_configurations()
        sut = self.get_sut(configurations)
        dumps = [configuration.dump() for configuration in configurations]
        non_void_dumps: Sequence[Dump] = [
            dump  # type: ignore[misc]
            for dump in dumps
            if dump is not Void
        ]
        assert non_void_dumps, "At least one configuration object must return a configuration dump that is not Void"
        for dump in non_void_dumps:
            sut.load_item(dump)


class TestProjectConfiguration:
    async def test_name(self) -> None:
        sut = ProjectConfiguration()
        name = "MyFirstBettySite"
        sut.name = name
        assert sut.name == name

    async def test_base_url(self) -> None:
        sut = ProjectConfiguration()
        base_url = "https://example.com"
        sut.base_url = base_url
        assert base_url == sut.base_url

    async def test_base_url_without_scheme_should_error(self) -> None:
        sut = ProjectConfiguration()
        with pytest.raises(AssertionFailed):
            sut.base_url = "/"

    async def test_base_url_without_path_should_error(self) -> None:
        sut = ProjectConfiguration()
        with pytest.raises(AssertionFailed):
            sut.base_url = "file://"

    async def test_root_path(self) -> None:
        sut = ProjectConfiguration()
        configured_root_path = "/betty/"
        expected_root_path = "betty"
        sut.root_path = configured_root_path
        assert expected_root_path == sut.root_path

    async def test_clean_urls(self) -> None:
        sut = ProjectConfiguration()
        clean_urls = True
        sut.clean_urls = clean_urls
        assert clean_urls == sut.clean_urls

    async def test_author_without_author(self) -> None:
        sut = ProjectConfiguration()
        assert sut.author is None

    async def test_author_with_author(self) -> None:
        sut = ProjectConfiguration()
        author = "Bart"
        sut.author = author
        assert author == sut.author

    async def test_load_should_load_minimal(self) -> None:
        dump: Any = ProjectConfiguration().dump()
        sut = ProjectConfiguration()
        sut.load(dump)
        assert dump["base_url"] == sut.base_url
        assert sut.title == "Betty"
        assert sut.author is None
        assert not sut.debug
        assert sut.root_path == ""
        assert not sut.clean_urls

    async def test_load_should_load_name(self) -> None:
        name = "MyFirstBettySite"
        dump: Any = ProjectConfiguration().dump()
        dump["name"] = name
        sut = ProjectConfiguration()
        sut.load(dump)
        assert sut.name == name

    async def test_load_should_load_title(self) -> None:
        title = "My first Betty site"
        dump: Any = ProjectConfiguration().dump()
        dump["title"] = title
        sut = ProjectConfiguration()
        sut.load(dump)
        assert sut.title == title

    async def test_load_should_load_author(self) -> None:
        author = "Bart"
        dump: Any = ProjectConfiguration().dump()
        dump["author"] = author
        sut = ProjectConfiguration()
        sut.load(dump)
        assert sut.author == author

    async def test_load_should_load_locale_locale(self) -> None:
        locale = "nl-NL"
        dump = ProjectConfiguration().dump()
        dump["locales"] = {
            locale: {},
        }
        sut = ProjectConfiguration()
        sut.load(dump)
        assert sut.locales == LocaleConfigurationMapping([LocaleConfiguration(locale)])

    async def test_load_should_load_locale_alias(self) -> None:
        locale = "nl-NL"
        alias = "nl"
        locale_config = {
            "alias": alias,
        }
        dump: Any = ProjectConfiguration().dump()
        dump["locales"] = {
            locale: locale_config,
        }
        sut = ProjectConfiguration()
        sut.load(dump)
        assert sut.locales == LocaleConfigurationMapping(
            [
                LocaleConfiguration(
                    locale,
                    alias=alias,
                ),
            ]
        )

    async def test_load_should_root_path(self) -> None:
        configured_root_path = "/betty/"
        expected_root_path = "betty"
        dump: Any = ProjectConfiguration().dump()
        dump["root_path"] = configured_root_path
        sut = ProjectConfiguration()
        sut.load(dump)
        assert sut.root_path == expected_root_path

    async def test_load_should_clean_urls(self) -> None:
        clean_urls = True
        dump: Any = ProjectConfiguration().dump()
        dump["clean_urls"] = clean_urls
        sut = ProjectConfiguration()
        sut.load(dump)
        assert sut.clean_urls == clean_urls

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_load_should_load_debug(self, debug: bool) -> None:
        dump: Any = ProjectConfiguration().dump()
        dump["debug"] = debug
        sut = ProjectConfiguration()
        sut.load(dump)
        assert sut.debug == debug

    async def test_load_should_load_one_extension_with_configuration(self) -> None:
        dump: Any = ProjectConfiguration().dump()
        extension_configuration = {
            "check": False,
        }
        dump["extensions"] = {
            _DummyConfigurableExtension.name(): {
                "configuration": extension_configuration,
            },
        }
        sut = ProjectConfiguration()
        expected = ExtensionConfiguration(
            _DummyConfigurableExtension,
            extension_configuration=_DummyConfigurableExtensionConfiguration(),
        )
        sut.load(dump)
        assert sut.extensions[_DummyConfigurableExtension] == expected

    async def test_load_should_load_one_extension_without_configuration(self) -> None:
        dump: Any = ProjectConfiguration().dump()
        dump["extensions"] = {
            _DummyNonConfigurableExtension.name(): {},
        }
        sut = ProjectConfiguration()
        expected = ExtensionConfiguration(_DummyNonConfigurableExtension)
        sut.load(dump)
        assert sut.extensions[_DummyNonConfigurableExtension] == expected

    async def test_load_extension_with_invalid_configuration_should_raise_error(
        self,
    ) -> None:
        dump: Any = ProjectConfiguration().dump()
        dump["extensions"] = {
            _DummyConfigurableExtension.name(): 1337,
        }
        sut = ProjectConfiguration()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_unknown_extension_type_name_should_error(self) -> None:
        dump: Any = ProjectConfiguration().dump()
        dump["extensions"] = {
            "non.existent.type": {},
        }
        sut = ProjectConfiguration()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_not_an_extension_type_name_should_error(self) -> None:
        dump: Any = ProjectConfiguration().dump()
        dump["extensions"] = {
            "%s.%s" % (self.__class__.__module__, self.__class__.__name__): {},
        }
        sut = ProjectConfiguration()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_load_should_error_if_invalid_config(self) -> None:
        dump: Dump = {}
        sut = ProjectConfiguration()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)

    async def test_dump_should_dump_minimal(self) -> None:
        sut = ProjectConfiguration()
        dump: Any = sut.dump()
        assert dump["base_url"] == sut.base_url
        assert sut.title == "Betty"
        assert sut.author is None
        assert not sut.debug
        assert sut.root_path == ""
        assert not sut.clean_urls

    async def test_dump_should_dump_title(self) -> None:
        title = "My first Betty site"
        sut = ProjectConfiguration()
        sut.title = title
        dump: Any = sut.dump()
        assert title == dump["title"]

    async def test_dump_should_dump_name(self) -> None:
        name = "MyFirstBettySite"
        sut = ProjectConfiguration()
        sut.name = name
        dump: Any = sut.dump()
        assert dump["name"] == name

    async def test_dump_should_dump_author(self) -> None:
        author = "Bart"
        sut = ProjectConfiguration()
        sut.author = author
        dump: Any = sut.dump()
        assert author == dump["author"]

    async def test_dump_should_dump_locale_locale(self) -> None:
        locale = "nl-NL"
        locale_configuration = LocaleConfiguration(locale)
        sut = ProjectConfiguration()
        sut.locales.append(locale_configuration)
        sut.locales.remove("en-US")
        dump: Any = sut.dump()
        assert dump["locales"] == {
            locale: {},
        }

    async def test_dump_should_dump_locale_alias(self) -> None:
        locale = "nl-NL"
        alias = "nl"
        locale_configuration = LocaleConfiguration(
            locale,
            alias=alias,
        )
        sut = ProjectConfiguration()
        sut.locales.append(locale_configuration)
        sut.locales.remove("en-US")
        dump: Any = sut.dump()
        assert dump["locales"] == {
            locale: {
                "alias": alias,
            },
        }

    async def test_dump_should_dump_root_path(self) -> None:
        root_path = "betty"
        sut = ProjectConfiguration()
        sut.root_path = root_path
        dump: Any = sut.dump()
        assert root_path == dump["root_path"]

    async def test_dump_should_dump_clean_urls(self) -> None:
        clean_urls = True
        sut = ProjectConfiguration()
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
    async def test_dump_should_dump_debug(self, debug: bool) -> None:
        sut = ProjectConfiguration()
        sut.debug = debug
        dump: Any = sut.dump()
        assert debug == dump["debug"]

    async def test_dump_should_dump_one_extension_with_configuration(self) -> None:
        sut = ProjectConfiguration()
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
        assert expected == dump["extensions"][_DummyConfigurableExtension.name()]

    async def test_dump_should_dump_one_extension_without_configuration(self) -> None:
        sut = ProjectConfiguration()
        sut.extensions.append(ExtensionConfiguration(_DummyNonConfigurableExtension))
        dump: Any = sut.dump()
        expected = {
            "enabled": True,
        }
        assert expected == dump["extensions"][_DummyNonConfigurableExtension.name()]

    async def test_dump_should_error_if_invalid_config(self) -> None:
        dump: Dump = {}
        sut = ProjectConfiguration()
        with raises_error(error_type=AssertionFailed):
            sut.load(dump)


class _DummyNonConfigurableExtension(Extension):
    pass


class _DummyEntity(Entity):
    pass


class _Tracker:
    async def track(self, carrier: list[Self]) -> None:
        raise NotImplementedError(repr(self))


class _TrackableExtension(Extension, _Tracker):
    async def track(self, carrier: list[Self]) -> None:
        carrier.append(self)


class _NonConfigurableExtension(_TrackableExtension):
    pass


class _ConfigurableExtensionConfiguration(Configuration):
    def __init__(self, check: int = 0):
        super().__init__()
        self.check = check

    def load(self, dump: Dump) -> None:
        assert_record(
            RequiredField("check", assert_int() | assert_setattr(self, "check"))
        )(dump)

    def dump(self) -> VoidableDump:
        return {"check": self.check}


class _CyclicDependencyOneExtension(Extension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_CyclicDependencyTwoExtension}


class _CyclicDependencyTwoExtension(Extension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_CyclicDependencyOneExtension}


class _DependsOnNonConfigurableExtensionExtension(_TrackableExtension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_NonConfigurableExtension}


class _AlsoDependsOnNonConfigurableExtensionExtension(_TrackableExtension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_NonConfigurableExtension}


class _DependsOnNonConfigurableExtensionExtensionExtension(_TrackableExtension):
    @classmethod
    def depends_on(cls) -> set[type[Extension]]:
        return {_DependsOnNonConfigurableExtensionExtension}


class _ComesBeforeNonConfigurableExtensionExtension(_TrackableExtension):
    @classmethod
    def comes_before(cls) -> set[type[Extension]]:
        return {_NonConfigurableExtension}


class _ComesAfterNonConfigurableExtensionExtension(_TrackableExtension):
    @classmethod
    def comes_after(cls) -> set[type[Extension]]:
        return {_NonConfigurableExtension}


class _ConfigurableExtension(
    ConfigurableExtension[_ConfigurableExtensionConfiguration]
):
    @classmethod
    def default_configuration(cls) -> _ConfigurableExtensionConfiguration:
        return _ConfigurableExtensionConfiguration(False)


class TestProject:
    async def test_extensions_with_one_extension(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        sut.configuration.extensions.append(
            ExtensionConfiguration(_NonConfigurableExtension)
        )
        async with sut:
            assert isinstance(
                sut.extensions[_NonConfigurableExtension], _NonConfigurableExtension
            )

    async def test_extensions_with_one_configurable_extension(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
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
            assert isinstance(
                sut.extensions[_ConfigurableExtension], _ConfigurableExtension
            )
            assert check == sut.extensions[_ConfigurableExtension].configuration.check

    async def test_extensions_with_one_extension_with_single_chained_dependency(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
        sut.configuration.extensions.append(
            ExtensionConfiguration(_DependsOnNonConfigurableExtensionExtensionExtension)
        )
        async with sut:
            carrier: list[_TrackableExtension] = []
            await sut.dispatcher.dispatch(_Tracker)(carrier)
            assert len(carrier) == 3
            assert isinstance(carrier[0], _NonConfigurableExtension)
            assert isinstance(carrier[1], _DependsOnNonConfigurableExtensionExtension)
            assert isinstance(
                carrier[2], _DependsOnNonConfigurableExtensionExtensionExtension
            )

    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
        sut.configuration.extensions.append(
            ExtensionConfiguration(_DependsOnNonConfigurableExtensionExtension)
        )
        sut.configuration.extensions.append(
            ExtensionConfiguration(_AlsoDependsOnNonConfigurableExtensionExtension)
        )
        async with sut:
            carrier: list[_TrackableExtension] = []
            await sut.dispatcher.dispatch(_Tracker)(carrier)
            assert len(carrier) == 3
            assert isinstance(carrier[0], _NonConfigurableExtension)
            assert _DependsOnNonConfigurableExtensionExtension in [
                type(extension) for extension in carrier
            ]
            assert _AlsoDependsOnNonConfigurableExtensionExtension in [
                type(extension) for extension in carrier
            ]

    async def test_extensions_with_multiple_extensions_with_cyclic_dependencies(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
        sut.configuration.extensions.append(
            ExtensionConfiguration(_CyclicDependencyOneExtension)
        )
        async with sut:
            with pytest.raises(CyclicDependencyError):  # noqa PT012
                sut.extensions  # noqa B018

    async def test_extensions_with_comes_before_with_other_extension(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
        sut.configuration.extensions.append(
            ExtensionConfiguration(_NonConfigurableExtension)
        )
        sut.configuration.extensions.append(
            ExtensionConfiguration(_ComesBeforeNonConfigurableExtensionExtension)
        )
        async with sut:
            carrier: list[_TrackableExtension] = []
            await sut.dispatcher.dispatch(_Tracker)(carrier)
            assert len(carrier) == 2
            assert isinstance(carrier[0], _ComesBeforeNonConfigurableExtensionExtension)
            assert isinstance(carrier[1], _NonConfigurableExtension)

    async def test_extensions_with_comes_before_without_other_extension(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
        sut.configuration.extensions.append(
            ExtensionConfiguration(_ComesBeforeNonConfigurableExtensionExtension)
        )
        async with sut:
            carrier: list[_TrackableExtension] = []
            await sut.dispatcher.dispatch(_Tracker)(carrier)
            assert len(carrier) == 1
            assert isinstance(carrier[0], _ComesBeforeNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_with_other_extension(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
        sut.configuration.extensions.append(
            ExtensionConfiguration(_ComesAfterNonConfigurableExtensionExtension)
        )
        sut.configuration.extensions.append(
            ExtensionConfiguration(_NonConfigurableExtension)
        )
        async with sut:
            carrier: list[_TrackableExtension] = []
            await sut.dispatcher.dispatch(_Tracker)(carrier)
            assert len(carrier) == 2
            assert isinstance(carrier[0], _NonConfigurableExtension)
            assert isinstance(carrier[1], _ComesAfterNonConfigurableExtensionExtension)

    async def test_extensions_with_comes_after_without_other_extension(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
        sut.configuration.extensions.append(
            ExtensionConfiguration(_ComesAfterNonConfigurableExtensionExtension)
        )
        async with sut:
            carrier: list[_TrackableExtension] = []
            await sut.dispatcher.dispatch(_Tracker)(carrier)
            assert len(carrier) == 1
            assert isinstance(carrier[0], _ComesAfterNonConfigurableExtensionExtension)

    async def test_ancestry_with___init___ancestry(
        self, new_temporary_app: App
    ) -> None:
        ancestry = Ancestry()
        sut = Project(new_temporary_app, ancestry=ancestry)
        async with sut:
            assert sut.ancestry is ancestry

    async def test_ancestry_without___init___ancestry(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            sut.ancestry  # noqa B018

    async def test_app(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            assert sut.app is new_temporary_app

    async def test_assets(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            assert len(sut.assets.paths) > 0

    async def test_discover_extension_types(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            assert len(sut.discover_extension_types()) > 0

    async def test_dispatcher(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            sut.dispatcher  # noqa B018

    async def test_entity_types(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            assert len(sut.entity_types) > 0

    async def test_event_types(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            assert len(sut.event_types) > 0

    async def test_jinja2_environment(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            sut.jinja2_environment  # noqa B018

    async def test_localizers(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            assert len(list(sut.localizers.locales)) > 0

    async def test_name_with_configuration_name(self, new_temporary_app: App) -> None:
        name = "hello-world"
        sut = Project(new_temporary_app)
        sut.configuration.name = name
        async with sut:
            assert sut.name == name

    async def test_name_without_configuration_name(
        self, new_temporary_app: App
    ) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            sut.name  # noqa B018

    async def test_renderer(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            sut.renderer  # noqa B018

    async def test_static_url_generator(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            sut.static_url_generator  # noqa B018

    async def test_url_generator(self, new_temporary_app: App) -> None:
        sut = Project(new_temporary_app)
        async with sut:
            sut.url_generator  # noqa B018
