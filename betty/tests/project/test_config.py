from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from babel import Locale
from typing_extensions import override

from betty.ancestry.event_type import EventTypeDefinition
from betty.ancestry.gender import GenderDefinition
from betty.ancestry.place_type import PlaceTypeDefinition
from betty.ancestry.presence_role import PresenceRoleDefinition
from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.exception import HumanFacingException
from betty.license import License, LicenseDefinition
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG, LocaleLike
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.machine_name import MachineName
from betty.model import Entity, EntityDefinition
from betty.plugin.config import PluginInstanceConfiguration
from betty.plugin.discovery.static import StaticDiscovery
from betty.plugin.repository.static import StaticPluginRepository
from betty.plugin.resolve import ResolvableId
from betty.project import Project
from betty.project.config import (
    CopyrightNoticePluginConfiguration,
    CopyrightNoticePluginConfigurationMapping,
    EntityTypeConfiguration,
    EntityTypeConfigurationMapping,
    EventTypePluginConfiguration,
    EventTypePluginConfigurationMapping,
    ExtensionInstanceConfigurationMapping,
    GenderPluginConfiguration,
    GenderPluginConfigurationMapping,
    LicensePluginConfiguration,
    LicensePluginConfigurationMapping,
    LocaleConfiguration,
    LocaleConfigurationMapping,
    PlaceTypePluginConfiguration,
    PlaceTypePluginConfigurationMapping,
    PresenceRolePluginConfiguration,
    PresenceRolePluginConfigurationMapping,
    ProjectConfiguration,
)
from betty.project.extension import Extension, ExtensionDefinition
from betty.test_utils.config import ConfigurationTestBase, DummyConfiguration
from betty.test_utils.config.collections import (
    ConfigurationCollectionTestBaseNewSut,
)
from betty.test_utils.config.collections.mapping import ConfigurationMappingTestBase
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.test_utils.model import DummyEntityOne, DummyNonPublicFacingEntityOne
from betty.test_utils.plugin.config import PluginDefinitionConfigurationMappingTestBase
from betty.test_utils.project.extension import (
    DummyConfigurableExtension,
    DummyExtensionOne,
)
from betty.typing import Void

if TYPE_CHECKING:
    from betty.app import App
    from betty.portable import PortableData, PortableMapping
    from betty.test_utils.config.collections import (
        ConfigurationCollectionTestBaseSutConfigurationKeys,
        ConfigurationCollectionTestBaseSutConfigurations,
    )


@ExtensionDefinition("dummy-non-configurable", label=DUMMY_LOCALIZABLE)
class _DummyNonConfigurableExtension(Extension):
    pass


class TestLocaleConfiguration(ConfigurationTestBase[LocaleConfiguration]):
    sut_cls = LocaleConfiguration

    async def test_locale(self) -> None:
        locale = Locale("nl")
        sut = LocaleConfiguration(locale)
        assert sut.locale is locale

    async def test_alias__implicit(self) -> None:
        locale = "nl-NL"
        sut = LocaleConfiguration(locale)
        assert sut.alias == locale

    async def test_alias__explicit(self) -> None:
        locale = "nl-NL"
        alias = "nl"
        sut = LocaleConfiguration(
            locale,
            alias=alias,
        )
        assert sut.alias == alias

    async def test_invalid_alias(self) -> None:
        locale = "nl-NL"
        alias = "/"
        with pytest.raises(HumanFacingException):
            LocaleConfiguration(
                locale,
                alias=alias,
            )

    async def test_load__with_invalid_dump(self) -> None:
        portable: PortableData = {}
        with pytest.raises(HumanFacingException):
            LocaleConfiguration.load(portable)

    async def test_load__with_locale(self) -> None:
        portable: PortableData = {
            "locale": DEFAULT_LOCALE_TAG,
        }
        sut = LocaleConfiguration.load(portable)
        assert sut.locale == DEFAULT_LOCALE

    async def test_load__with_alias(self) -> None:
        portable: PortableData = {
            "locale": "nl-NL",
            "alias": "my-first-alias",
        }
        sut = LocaleConfiguration.load(portable)
        assert sut.alias == "my-first-alias"

    async def test_dump__should_dump_minimal(self) -> None:
        sut = LocaleConfiguration("nl-NL")
        expected = {
            "locale": "nl-NL",
        }
        assert sut.dump() == expected

    async def test_dump__should_dump_alias(self) -> None:
        sut = LocaleConfiguration("nl-NL", alias="nl")
        expected = {"locale": "nl-NL", "alias": "nl"}
        assert sut.dump() == expected


LocaleConfigurationMappingTestNewSut = ConfigurationCollectionTestBaseNewSut[
    LocaleConfiguration, Locale, LocaleLike
]


class TestLocaleConfigurationMapping(
    ConfigurationMappingTestBase[
        LocaleConfigurationMapping, Locale, LocaleLike, LocaleConfiguration
    ]
):
    sut_cls = LocaleConfigurationMapping

    @override
    @pytest.fixture
    def new_sut(self) -> LocaleConfigurationMappingTestNewSut:
        return LocaleConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[Locale]:
        return (
            Locale("en"),
            Locale("nl"),
            Locale("uk"),
            Locale("fr"),
        )

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[LocaleConfiguration]:
        return (
            LocaleConfiguration("en"),
            LocaleConfiguration("nl"),
            LocaleConfiguration("uk"),
            LocaleConfiguration("fr"),
        )

    @override
    def test___delitem__(  # type: ignore[override]
        self,
        new_sut: LocaleConfigurationMappingTestNewSut,
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:
        sut = new_sut([sut_configurations[0]])
        del sut[sut_configurations[0].locale]
        with pytest.raises(KeyError):
            sut[sut_configurations[0].locale]
        assert len(sut) == 1
        assert DEFAULT_LOCALE in sut

    def test___delitem____with_locale(
        self,
        new_sut: LocaleConfigurationMappingTestNewSut,
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:
        sut = new_sut([sut_configurations[0], sut_configurations[1]])
        del sut[sut_configurations[0].locale]
        with pytest.raises(KeyError):
            sut[sut_configurations[0].locale]

    def test___delitem____with_one_remaining_locale_configuration(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        sut = LocaleConfigurationMapping(
            [
                locale_configuration_a,
            ]
        )
        del sut["nl-NL"]
        assert len(sut) == 1
        assert DEFAULT_LOCALE in sut

    def test_default__without_explicit_locale_configurations(self) -> None:
        sut = LocaleConfigurationMapping()
        assert sut.default.locale == DEFAULT_LOCALE

    def test_default__without_explicit_default(self) -> None:
        locale_configuration_a = LocaleConfiguration("nl-NL")
        locale_configuration_b = LocaleConfiguration("en-US")
        sut = LocaleConfigurationMapping(
            [
                locale_configuration_a,
                locale_configuration_b,
            ]
        )
        assert sut.default == locale_configuration_a

    @override
    def test_replace__without_items(  # type: ignore[override]
        self,
        sut: LocaleConfigurationMapping,
    ) -> None:
        sut.clear()
        assert len(sut) == 1
        sut.replace()
        assert len(sut) == 1

    @override
    def test_replace__with_items(  # type: ignore[override]
        self,
        sut: LocaleConfigurationMapping,
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:
        sut.clear()
        assert len(sut) == 1
        sut.replace(*sut_configurations)
        assert len(sut) == len(sut_configurations)

    def test_multilingual__with_one_configuration(
        self, sut: LocaleConfigurationMapping
    ) -> None:
        assert not sut.multilingual

    def test_multilingual__with_multiple_configurations(
        self,
        sut: LocaleConfigurationMapping,
        sut_configurations: ConfigurationCollectionTestBaseSutConfigurations[
            LocaleConfiguration
        ],
    ) -> None:
        sut.replace(*sut_configurations)
        assert sut.multilingual


@ExtensionDefinition(
    "extension-instance-configuration-mapping-test-extension-0",
    label=DUMMY_LOCALIZABLE,
)
class ExtensionInstanceConfigurationMappingTestExtension0(Extension):
    pass


@ExtensionDefinition(
    "extension-instance-configuration-mapping-test-extension-1",
    label=DUMMY_LOCALIZABLE,
)
class ExtensionInstanceConfigurationMappingTestExtension1(Extension):
    pass


@ExtensionDefinition(
    "extension-instance-configuration-mapping-test-extension-2",
    label=DUMMY_LOCALIZABLE,
)
class ExtensionInstanceConfigurationMappingTestExtension2(Extension):
    pass


@ExtensionDefinition(
    "extension-instance-configuration-mapping-test-extension-3",
    label=DUMMY_LOCALIZABLE,
)
class ExtensionInstanceConfigurationMappingTestExtension3(Extension):
    pass


class TestExtensionInstanceConfigurationMapping(
    ConfigurationMappingTestBase[
        ExtensionInstanceConfigurationMapping,
        MachineName,
        ResolvableId[ExtensionDefinition],
        PluginInstanceConfiguration[ExtensionDefinition, Extension],
    ]
):
    sut_cls = ExtensionInstanceConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return (
            ExtensionInstanceConfigurationMappingTestExtension0.plugin().id,
            ExtensionInstanceConfigurationMappingTestExtension1.plugin().id,
            ExtensionInstanceConfigurationMappingTestExtension2.plugin().id,
            ExtensionInstanceConfigurationMappingTestExtension3.plugin().id,
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PluginInstanceConfiguration[ExtensionDefinition, Extension],
        MachineName,
        ResolvableId[ExtensionDefinition],
    ]:
        return ExtensionInstanceConfigurationMapping

    @override
    @pytest.fixture
    def sut_configurations(
        self,
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            MachineName
        ],
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PluginInstanceConfiguration[ExtensionDefinition, Extension]
    ]:
        return (
            PluginInstanceConfiguration(sut_configuration_keys[0]),
            PluginInstanceConfiguration(sut_configuration_keys[1]),
            PluginInstanceConfiguration(sut_configuration_keys[2]),
            PluginInstanceConfiguration(sut_configuration_keys[3]),
        )

    def test_enable(self) -> None:
        sut = ExtensionInstanceConfigurationMapping()
        sut.enable(DummyExtensionOne)
        assert DummyExtensionOne.plugin() in sut


class TestEntityTypeConfiguration(ConfigurationTestBase[EntityTypeConfiguration]):
    sut_cls = EntityTypeConfiguration

    async def test_id__with___init___entity_type(self) -> None:
        entity_type = DummyEntityOne
        sut = EntityTypeConfiguration(entity_type)
        assert sut.id == entity_type.plugin().id

    async def test_id__with___init___entity_type_id(self) -> None:
        entity_type_id = DummyEntityOne.plugin().id
        sut = EntityTypeConfiguration(entity_type_id)
        assert sut.id == entity_type_id

    @pytest.mark.parametrize(
        "generate_html_list,",
        [
            True,
            False,
        ],
    )
    async def test_generate_html_list(self, generate_html_list: bool) -> None:
        sut = EntityTypeConfiguration(DummyEntityOne)
        sut.generate_html_list = generate_html_list
        assert sut.generate_html_list == generate_html_list

    async def test_load__with_empty_configuration(self) -> None:
        portable: PortableData = {}
        with pytest.raises(HumanFacingException):
            EntityTypeConfiguration.load(portable)

    def test_load__with_minimal_configuration(self) -> None:
        portable: PortableData = {
            "entity_type": DummyEntityOne.plugin().id,
        }
        EntityTypeConfiguration.load(portable)

    @pytest.mark.parametrize(
        "generate_html_list,",
        [
            True,
            False,
        ],
    )
    def test_load__with_generate_html_list(self, generate_html_list: bool) -> None:
        portable: PortableData = {
            "entity_type": DummyEntityOne.plugin().id,
            "generate_html_list": generate_html_list,
        }
        sut = EntityTypeConfiguration.load(portable)
        assert sut.generate_html_list == generate_html_list

    async def test_dump__with_minimal_configuration(self) -> None:
        sut = EntityTypeConfiguration(DummyEntityOne)
        expected = {
            "entity_type": DummyEntityOne.plugin().id,
            "generate_html_list": False,
        }
        assert sut.dump() == expected

    async def test_dump__with_generate_html_list(self) -> None:
        sut = EntityTypeConfiguration(DummyEntityOne, generate_html_list=False)
        expected = {
            "entity_type": DummyEntityOne.plugin().id,
            "generate_html_list": False,
        }
        assert sut.dump() == expected

    async def test_validate__with_generate_html_list_with_non_public_facing_entity_type_should_error(
        self,
    ) -> None:
        sut = EntityTypeConfiguration(
            DummyNonPublicFacingEntityOne, generate_html_list=True
        )
        with pytest.raises(HumanFacingException):
            await sut.validate(
                StaticPluginRepository(EntityDefinition, DummyNonPublicFacingEntityOne)
            )


@EntityDefinition(
    "zero",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class EntityTypeConfigurationMappingTestEntity0(Entity):
    pass


@EntityDefinition(
    "one",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class EntityTypeConfigurationMappingTestEntity1(Entity):
    pass


@EntityDefinition(
    "two",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class EntityTypeConfigurationMappingTestEntity2(Entity):
    pass


@EntityDefinition(
    "three",
    label=DUMMY_LOCALIZABLE,
    label_plural=DUMMY_LOCALIZABLE,
    label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
)
class EntityTypeConfigurationMappingTestEntity3(Entity):
    pass


class TestEntityTypeConfigurationMapping(
    ConfigurationMappingTestBase[
        EntityTypeConfigurationMapping,
        MachineName,
        ResolvableId[EntityDefinition],
        EntityTypeConfiguration,
    ]
):
    sut_cls = EntityTypeConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return (
            EntityTypeConfigurationMappingTestEntity0.plugin().id,
            EntityTypeConfigurationMappingTestEntity1.plugin().id,
            EntityTypeConfigurationMappingTestEntity2.plugin().id,
            EntityTypeConfigurationMappingTestEntity3.plugin().id,
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        EntityTypeConfiguration, MachineName, ResolvableId[EntityDefinition]
    ]:
        return EntityTypeConfigurationMapping

    @override
    @pytest.fixture
    def sut_configurations(
        self,
        sut_configuration_keys: ConfigurationCollectionTestBaseSutConfigurationKeys[
            MachineName
        ],
    ) -> ConfigurationCollectionTestBaseSutConfigurations[EntityTypeConfiguration]:
        return (
            EntityTypeConfiguration(sut_configuration_keys[0]),
            EntityTypeConfiguration(sut_configuration_keys[1]),
            EntityTypeConfiguration(sut_configuration_keys[2]),
            EntityTypeConfiguration(sut_configuration_keys[3]),
        )

    async def test_validate__with_item_error_should_error(self) -> None:
        sut = EntityTypeConfigurationMapping(
            [
                EntityTypeConfiguration(
                    DummyNonPublicFacingEntityOne, generate_html_list=True
                )
            ]
        )
        with pytest.raises(HumanFacingException):
            await sut.validate(
                StaticPluginRepository(EntityDefinition, DummyNonPublicFacingEntityOne)
            )


class TestCopyrightNoticePluginConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        CopyrightNoticePluginConfigurationMapping,
        CopyrightNoticeDefinition,
        CopyrightNoticePluginConfiguration,
    ]
):
    sut_cls = CopyrightNoticePluginConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        CopyrightNoticePluginConfiguration
    ]:
        return (
            CopyrightNoticePluginConfiguration(
                id="foo",
                label="Foo",
                summary=DUMMY_LOCALIZABLE,
                text=DUMMY_LOCALIZABLE,
            ),
            CopyrightNoticePluginConfiguration(
                id="bar",
                label="Bar",
                summary=DUMMY_LOCALIZABLE,
                text=DUMMY_LOCALIZABLE,
            ),
            CopyrightNoticePluginConfiguration(
                id="baz",
                label="Baz",
                summary=DUMMY_LOCALIZABLE,
                text=DUMMY_LOCALIZABLE,
            ),
            CopyrightNoticePluginConfiguration(
                id="qux",
                label="Qux",
                summary=DUMMY_LOCALIZABLE,
                text=DUMMY_LOCALIZABLE,
            ),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        CopyrightNoticePluginConfiguration,
        MachineName,
        ResolvableId[CopyrightNoticeDefinition],
    ]:
        return CopyrightNoticePluginConfigurationMapping


class TestLicensePluginConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        LicensePluginConfigurationMapping, LicenseDefinition, LicensePluginConfiguration
    ]
):
    sut_cls = LicensePluginConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[LicensePluginConfiguration]:
        return (
            LicensePluginConfiguration(
                id="foo",
                label="Foo",
                summary=DUMMY_LOCALIZABLE,
                text=DUMMY_LOCALIZABLE,
            ),
            LicensePluginConfiguration(
                id="bar",
                label="Bar",
                summary=DUMMY_LOCALIZABLE,
                text=DUMMY_LOCALIZABLE,
            ),
            LicensePluginConfiguration(
                id="baz",
                label="Baz",
                summary=DUMMY_LOCALIZABLE,
                text=DUMMY_LOCALIZABLE,
            ),
            LicensePluginConfiguration(
                id="qux",
                label="Qux",
                summary=DUMMY_LOCALIZABLE,
                text=DUMMY_LOCALIZABLE,
            ),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        LicensePluginConfiguration,
        MachineName,
        ResolvableId[LicenseDefinition],
    ]:
        return LicensePluginConfigurationMapping


class TestEventTypePluginConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        EventTypePluginConfigurationMapping,
        EventTypeDefinition,
        EventTypePluginConfiguration,
    ]
):
    sut_cls = EventTypePluginConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[EventTypePluginConfiguration]:
        return (
            EventTypePluginConfiguration(
                id="foo",
                label="Foo",
                label_plural="Foo",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            EventTypePluginConfiguration(
                id="bar",
                label="Bar",
                label_plural="Bar",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            EventTypePluginConfiguration(
                id="baz",
                label="Baz",
                label_plural="Baz",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            EventTypePluginConfiguration(
                id="qux",
                label="Qux",
                label_plural="Qux",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        EventTypePluginConfiguration,
        MachineName,
        ResolvableId[EventTypeDefinition],
    ]:
        return EventTypePluginConfigurationMapping


class TestPlaceTypePluginConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        PlaceTypePluginConfigurationMapping,
        PlaceTypeDefinition,
        PlaceTypePluginConfiguration,
    ]
):
    sut_cls = PlaceTypePluginConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[PlaceTypePluginConfiguration]:
        return (
            PlaceTypePluginConfiguration(
                id="foo",
                label="Foo",
                label_plural="Foo",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            PlaceTypePluginConfiguration(
                id="bar",
                label="Bar",
                label_plural="Bar",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            PlaceTypePluginConfiguration(
                id="baz",
                label="Baz",
                label_plural="Baz",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            PlaceTypePluginConfiguration(
                id="qux",
                label="Qux",
                label_plural="Qux",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PlaceTypePluginConfiguration,
        MachineName,
        ResolvableId[PlaceTypeDefinition],
    ]:
        return PlaceTypePluginConfigurationMapping


class TestPresenceRolePluginConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        PresenceRolePluginConfigurationMapping,
        PresenceRoleDefinition,
        PresenceRolePluginConfiguration,
    ]
):
    sut_cls = PresenceRolePluginConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[
        PresenceRolePluginConfiguration
    ]:
        return (
            PresenceRolePluginConfiguration(
                id="foo",
                label="Foo",
                label_plural="Foo",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            PresenceRolePluginConfiguration(
                id="bar",
                label="Bar",
                label_plural="Bar",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            PresenceRolePluginConfiguration(
                id="baz",
                label="Baz",
                label_plural="Baz",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            PresenceRolePluginConfiguration(
                id="qux",
                label="Qux",
                label_plural="Qux",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        PresenceRolePluginConfiguration,
        MachineName,
        ResolvableId[PresenceRoleDefinition],
    ]:
        return PresenceRolePluginConfigurationMapping


class TestGenderPluginConfigurationMapping(
    PluginDefinitionConfigurationMappingTestBase[
        GenderPluginConfigurationMapping, GenderDefinition, GenderPluginConfiguration
    ]
):
    sut_cls = GenderPluginConfigurationMapping

    @override
    @pytest.fixture
    def sut_configuration_keys(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurationKeys[MachineName]:
        return "foo", "bar", "baz", "qux"

    @override
    @pytest.fixture
    def sut_configurations(
        self,
    ) -> ConfigurationCollectionTestBaseSutConfigurations[GenderPluginConfiguration]:
        return (
            GenderPluginConfiguration(
                id="foo",
                label="Foo",
                label_plural="Foo",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            GenderPluginConfiguration(
                id="bar",
                label="Bar",
                label_plural="Bar",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            GenderPluginConfiguration(
                id="baz",
                label="Baz",
                label_plural="Baz",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
            GenderPluginConfiguration(
                id="qux",
                label="Qux",
                label_plural="Qux",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
        )

    @override
    @pytest.fixture
    def new_sut(
        self,
    ) -> ConfigurationCollectionTestBaseNewSut[
        GenderPluginConfiguration, MachineName, ResolvableId[GenderDefinition]
    ]:
        return GenderPluginConfigurationMapping


class TestProjectConfiguration(ConfigurationTestBase[ProjectConfiguration]):
    sut_cls = ProjectConfiguration

    async def test_validator__should_validate_entity_type_configuration(
        self, isolated_app: App
    ) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.entity_types.replace(
            EntityTypeConfiguration(
                DummyNonPublicFacingEntityOne.plugin(), generate_html_list=True
            )
        )
        with EntityDefinition.type().override_discovery(
            StaticDiscovery(DummyNonPublicFacingEntityOne)
        ):
            async with Project.new_isolated(isolated_app) as project:
                async with project:
                    with pytest.raises(HumanFacingException) as exc_info:
                        await project.new_target(sut.validator)
        assert 'data["entity_types"]["dummy-non-public-facing-one"]' in str(
            exc_info.value
        )

    async def test_lifetime_threshold(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.lifetime_threshold = 999
        assert sut.lifetime_threshold == 999

    async def test_locales(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert DEFAULT_LOCALE in sut.locales

    async def test_extensions(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert len(sut.extensions) == 0

    async def test_entity_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.entity_types  # noqa: B018

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_debug(self, debug: bool) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.debug = debug
        assert sut.debug == debug

    async def test_title(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        title = Plain("My First Betty Site")
        sut.title = title
        assert sut.title is title

    async def test_name(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        name = "my-first-betty-site"
        sut.name = name
        assert sut.name == name

    async def test_url(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        url = "https://example.com/example"
        sut.url = url
        assert sut.url == url

    async def test_url__without_scheme_should_error(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        with pytest.raises(HumanFacingException):
            sut.url = "/"

    async def test_url__without_path_should_error(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        with pytest.raises(HumanFacingException):
            sut.url = "file://"

    @pytest.mark.parametrize(
        ("expected", "url"),
        [
            ("https://example.com", "https://example.com"),
            ("https://example.com", "https://example.com/"),
            ("https://example.com", "https://example.com/root-path"),
        ],
    )
    async def test_base_url(self, expected: str, url: str) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.url = url
        assert sut.base_url == expected

    @pytest.mark.parametrize(
        ("expected", "url"),
        [
            ("", "https://example.com"),
            ("", "https://example.com/"),
            ("/root-path", "https://example.com/root-path"),
            ("/root-path", "https://example.com/root-path/"),
        ],
    )
    async def test_root_path(self, expected: str, url: str) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.url = url
        assert sut.root_path == expected

    async def test_clean_urls(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        clean_urls = True
        sut.clean_urls = clean_urls
        assert sut.clean_urls == clean_urls

    async def test_author__without_author(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.author is None

    async def test_author__with_author(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        author = Plain("Bart")
        sut.author = author
        assert sut.author is author

    async def test___init____with_logo(self) -> None:
        logo = Path("logo.png")
        sut = ProjectConfiguration(logo=logo, title="Betty", url="https://example.com")
        assert sut.logo == logo

    async def test_logo(self) -> None:
        logo = Path("logo.png")
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.logo = logo
        assert sut.logo == logo

    async def test_copyright_notices(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.copyright_notices is sut.copyright_notices

    async def test_licenses(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.licenses is sut.licenses

    async def test_event_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.event_types is sut.event_types

    async def test_place_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.place_types is sut.place_types

    async def test_presence_roles(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.presence_roles is sut.presence_roles

    async def test_genders(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.genders is sut.genders

    async def test_load__should_load_minimal(self) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        sut = ProjectConfiguration.load(portable)
        assert sut.url == portable["url"]

    async def test_load__should_load_name(self) -> None:
        name = "my-first-betty-site"
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["name"] = name
        sut = ProjectConfiguration.load(portable)
        assert sut.name == name

    async def test_load__should_load_title(self) -> None:
        title = "My first Betty site"
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["title"] = title
        sut = ProjectConfiguration.load(portable)
        assert sut.title.localize(DEFAULT_LOCALIZER) == title

    async def test_load__should_load_copyright_notice(self) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        copyright_notice_id = "my-first-copyright-notice"
        portable["copyright_notice"] = copyright_notice_id
        sut = ProjectConfiguration.load(portable)
        assert sut.copyright_notice.id == copyright_notice_id

    async def test_load__should_load_copyright_notices(self) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        copyright_notice_id = "my-first-copyright-notice"
        copyright_notice_label = "My First Copyright Notice"
        portable["copyright_notices"] = {
            copyright_notice_id: {
                "label": copyright_notice_label,
                "summary": "This is My First Copyright Notice.",
                "text": "My First Copyright Notice is the best copyright notice.",
            }
        }
        sut = ProjectConfiguration.load(portable)
        assert (
            sut.copyright_notices[copyright_notice_id].label.localize(DEFAULT_LOCALIZER)
            == copyright_notice_label
        )

    async def test_load__should_load_license(self) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        license_id = "my-first-license"
        portable["license"] = license_id
        sut = ProjectConfiguration.load(portable)
        assert sut.license.id == license_id

    async def test_load__should_load_licenses(self) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        license_id = "my-first-license"
        license_label = "My First License"
        portable["licenses"] = {
            license_id: {
                "label": license_label,
                "summary": "This is My First License.",
                "text": "My First License is the best license.",
            }
        }
        sut = ProjectConfiguration.load(portable)
        assert (
            sut.licenses[license_id].label.localize(DEFAULT_LOCALIZER) == license_label
        )

    async def test_load__should_load_author(self) -> None:
        author = "Bart"
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["author"] = author
        sut = ProjectConfiguration.load(portable)
        assert sut.author is not None
        assert sut.author.localize(DEFAULT_LOCALIZER) == author

    async def test_load__should_load_logo(self) -> None:
        logo = Path("logo.png")
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["logo"] = str(logo)
        sut = ProjectConfiguration.load(portable)
        assert sut.logo == logo

    async def test_load__should_load_locale_locale(self) -> None:
        locale = "nl-NL"
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["locales"] = [{"locale": locale}]
        sut = ProjectConfiguration.load(portable)
        assert len(sut.locales) == 1
        assert locale in sut.locales

    async def test_load__should_load_locale_alias(self) -> None:
        locale = "nl-NL"
        alias = "nl"
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["locales"] = [{"locale": locale, "alias": alias}]
        sut = ProjectConfiguration.load(portable)
        assert len(sut.locales) == 1
        assert locale in sut.locales
        actual = sut.locales[locale]
        assert actual.alias == alias

    async def test_load__should_clean_urls(self) -> None:
        clean_urls = True
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["clean_urls"] = clean_urls
        sut = ProjectConfiguration.load(portable)
        assert sut.clean_urls == clean_urls

    @pytest.mark.parametrize(
        "debug",
        [
            True,
            False,
        ],
    )
    async def test_load__should_load_debug(self, debug: bool) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["debug"] = debug
        sut = ProjectConfiguration.load(portable)
        assert sut.debug == debug

    async def test_load__should_load_extension(self) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["extensions"] = {
            DummyExtensionOne.plugin().id: {},
        }
        sut = ProjectConfiguration.load(portable)
        actual = sut.extensions[DummyExtensionOne.plugin()]
        assert isinstance(actual.configuration, Void)

    async def test_load__extension_with_invalid_configuration_should_raise_error(
        self,
    ) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["extensions"] = {
            DummyConfigurableExtension.plugin().id: 1337,
        }
        with pytest.raises(HumanFacingException):
            ProjectConfiguration.load(portable)

    @pytest.mark.parametrize(
        ("expected", "event_types_configuration"),
        [
            ({}, {}),
            (
                {
                    "foo": {
                        "label": "Foo",
                        "label_plural": "Foos",
                        "label_countable": {
                            "en-US": {
                                "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                                "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                            },
                        },
                    }
                },
                {
                    "foo": {
                        "label": "Foo",
                        "label_plural": "Foos",
                        "label_countable": {
                            "en-US": {
                                "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                                "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                            },
                        },
                    }
                },
            ),
        ],
    )
    async def test_load__should_load_event_types(
        self,
        expected: PortableMapping,
        event_types_configuration: PortableMapping,
    ) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["event_types"] = event_types_configuration
        sut = ProjectConfiguration.load(portable)
        if event_types_configuration:
            assert sut.dump()["event_types"] == expected

    @pytest.mark.parametrize(
        ("expected", "place_types_configuration"),
        [
            ({}, {}),
            (
                {
                    "foo": {
                        "label": "Foo",
                        "label_plural": "Foos",
                        "label_countable": {
                            "en-US": {
                                "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                                "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                            },
                        },
                    }
                },
                {
                    "foo": {
                        "label": "Foo",
                        "label_plural": "Foos",
                        "label_countable": {
                            "en-US": {
                                "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                                "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                            },
                        },
                    }
                },
            ),
        ],
    )
    async def test_load__should_load_place_types(
        self,
        expected: PortableMapping,
        place_types_configuration: PortableMapping,
    ) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["place_types"] = place_types_configuration
        sut = ProjectConfiguration.load(portable)
        if place_types_configuration:
            assert sut.dump()["place_types"] == expected

    @pytest.mark.parametrize(
        ("expected", "presence_roles_configuration"),
        [
            ({}, {}),
            (
                {
                    "foo": {
                        "label": "Foo",
                        "label_countable": {
                            "en-US": {
                                "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                                "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                            },
                        },
                        "label_plural": "Foo",
                    }
                },
                {
                    "foo": {
                        "label": "Foo",
                        "label_countable": {
                            "en-US": {
                                "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                                "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                            },
                        },
                        "label_plural": "Foo",
                    }
                },
            ),
        ],
    )
    async def test_load__should_load_presence_roles(
        self,
        expected: PortableMapping,
        presence_roles_configuration: PortableMapping,
    ) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["presence_roles"] = presence_roles_configuration
        sut = ProjectConfiguration.load(portable)
        if presence_roles_configuration:
            assert sut.dump()["presence_roles"] == expected

    @pytest.mark.parametrize(
        ("expected", "genders_configuration"),
        [
            ({}, {}),
            (
                {
                    "foo": {
                        "label": "Foo",
                        "label_countable": {
                            "en-US": {
                                "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                                "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                            },
                        },
                        "label_plural": "Foo",
                    }
                },
                {
                    "foo": {
                        "label": "Foo",
                        "label_countable": {
                            "en-US": {
                                "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                                "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                            },
                        },
                        "label_plural": "Foo",
                    }
                },
            ),
        ],
    )
    async def test_load__should_load_genders(
        self,
        expected: PortableMapping,
        genders_configuration: PortableMapping,
    ) -> None:
        portable = ProjectConfiguration(title="Betty", url="https://example.com").dump()
        portable["genders"] = genders_configuration
        sut = ProjectConfiguration.load(portable)
        if genders_configuration:
            assert sut.dump()["genders"] == expected

    async def test_load__should_error_if_invalid_config(self) -> None:
        portable: PortableData = {}
        with pytest.raises(HumanFacingException):
            ProjectConfiguration.load(portable)

    async def test_dump__should_dump_minimal(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        assert sut.dump() == {
            "title": "Betty",
            "url": "https://example.com",
        }

    async def test_dump__should_dump_title(self) -> None:
        title = "My first Betty site"
        portable = ProjectConfiguration(title=title, url="https://example.com").dump()
        assert portable["title"] == title

    async def test_dump__should_dump_name(self) -> None:
        name = "my-first-betty-site"
        portable = ProjectConfiguration(
            name=name, title="Betty", url="https://example.com"
        ).dump()
        assert portable["name"] == name

    async def test_dump__should_dump_author(self) -> None:
        author = "Bart"
        portable = ProjectConfiguration(
            author=author, title="Betty", url="https://example.com"
        ).dump()
        assert portable["author"] == author

    async def test_dump__should_dumpo_logo(self) -> None:
        logo = Path("logo.png")
        portable = ProjectConfiguration(
            logo=logo, title="Betty", url="https://example.com"
        ).dump()
        assert portable["logo"] == str(logo)

    async def test_dump__should_dump_locale_locale(self) -> None:
        locale = "nl-NL"
        locale_configuration = LocaleConfiguration(locale)
        portable = ProjectConfiguration(
            locales=LocaleConfigurationMapping([locale_configuration]),
            title="Betty",
            url="https://example.com",
        ).dump()
        assert portable["locales"] == [
            {
                "locale": locale,
            },
        ]

    async def test_dump__should_dump_locale_alias(self) -> None:
        locale = "nl-NL"
        alias = "nl"
        locale_configuration = LocaleConfiguration(
            locale,
            alias=alias,
        )
        portable = ProjectConfiguration(
            locales=LocaleConfigurationMapping([locale_configuration]),
            title="Betty",
            url="https://example.com",
        ).dump()
        assert portable["locales"] == [
            {"locale": locale, "alias": alias},
        ]

    async def test_dump__should_dump_clean_urls(self) -> None:
        clean_urls = True
        portable = ProjectConfiguration(
            clean_urls=clean_urls, title="Betty", url="https://example.com"
        ).dump()
        assert portable["clean_urls"] == clean_urls

    async def test_dump__should_dump_debug(self) -> None:
        portable = ProjectConfiguration(
            debug=True, title="Betty", url="https://example.com"
        ).dump()
        assert portable["debug"]

    async def test_dump__should_dump_one_extension_with_configuration(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        value = "Hello, world!"
        sut.extensions.append(
            PluginInstanceConfiguration(
                DummyConfigurableExtension.plugin(), DummyConfiguration(value)
            )
        )
        portable = sut.dump()
        expected = {
            DummyConfigurableExtension.plugin().id: {
                "configuration": {
                    "value": value,
                },
            }
        }
        assert portable["extensions"] == expected

    async def test_dump__should_dump_one_extension_without_configuration(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.extensions.enable(_DummyNonConfigurableExtension)
        portable = sut.dump()
        expected: PortableData = {_DummyNonConfigurableExtension.plugin().id: {}}
        assert portable["extensions"] == expected

    async def test_dump__should_dump_event_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.event_types.append(
            EventTypePluginConfiguration(
                id="foo",
                label="Foo",
                label_plural="Foos",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            )
        )
        portable = sut.dump()
        expected: PortableMapping = {
            "foo": {
                "label": "Foo",
                "label_plural": "Foos",
                "label_countable": {
                    "en-US": {
                        "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                        "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                    },
                },
            }
        }
        assert portable["event_types"] == expected

    async def test_dump__should_dump_place_types(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.place_types.append(
            PlaceTypePluginConfiguration(
                id="foo",
                label="Foo",
                label_plural="Foos",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            )
        )
        portable = sut.dump()
        expected: PortableMapping = {
            "foo": {
                "label": "Foo",
                "label_plural": "Foos",
                "label_countable": {
                    "en-US": {
                        "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                        "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                    },
                },
            }
        }
        assert portable["place_types"] == expected

    async def test_dump__should_dump_presence_roles(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.presence_roles.append(
            PresenceRolePluginConfiguration(
                id="foo",
                label="Foo",
                label_plural="Foos",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            ),
        )
        portable = sut.dump()
        expected: PortableMapping = {
            "foo": {
                "label": "Foo",
                "label_plural": "Foos",
                "label_countable": {
                    "en-US": {
                        "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                        "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                    },
                },
            }
        }
        assert portable["presence_roles"] == expected

    async def test_dump__should_dump_genders(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        sut.genders.append(
            GenderPluginConfiguration(
                id="foo",
                label="Foo",
                label_plural="Foos",
                label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
            )
        )
        portable = sut.dump()
        expected: PortableMapping = {
            "foo": {
                "label": "Foo",
                "label_plural": "Foos",
                "label_countable": {
                    "en-US": {
                        "one": "{count} DUMMY_COUNTABLE_LOCALIZABLE",
                        "other": "{count} DUMMY_COUNTABLE_LOCALIZABLES",
                    },
                },
            }
        }
        assert portable["genders"] == expected

    async def test_dump__should_dump_copyright_notice(self) -> None:
        copyright_notice_configuration = PluginInstanceConfiguration[
            CopyrightNoticeDefinition, CopyrightNotice
        ]("-")
        sut = ProjectConfiguration(
            copyright_notice=copyright_notice_configuration,
            title="Betty",
            url="https://example.com",
        )
        assert sut.dump()["copyright_notice"] == copyright_notice_configuration.id

    async def test_dump__should_dump_copyright_notices(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        copyright_notice_id = "my-first-copyright-notice"
        copyright_notice_label = "My First Copyright Notice"
        copyright_notice_summary = "This is My First Copyright Notice."
        copyright_notice_text = (
            "My First Copyright Notice is the best copyright notice."
        )
        sut.copyright_notices.append(
            CopyrightNoticePluginConfiguration(
                id=copyright_notice_id,
                label=copyright_notice_label,
                summary=copyright_notice_summary,
                text=copyright_notice_text,
            )
        )
        assert sut.dump()["copyright_notices"] == {
            copyright_notice_id: {
                "label": copyright_notice_label,
                "summary": copyright_notice_summary,
                "text": copyright_notice_text,
            }
        }

    async def test_dump__should_dump_license(self) -> None:
        license_configuration = PluginInstanceConfiguration[LicenseDefinition, License](
            "-"
        )
        sut = ProjectConfiguration(
            license=license_configuration, title="Betty", url="https://example.com"
        )
        assert sut.dump()["license"] == license_configuration.id

    async def test_dump__should_dump_licenses(self) -> None:
        sut = ProjectConfiguration(title="Betty", url="https://example.com")
        license_id = "my-first-license"
        license_label = "My First License"
        license_summary = "This is My First License."
        license_text = "My First License is the best license."
        sut.licenses.append(
            LicensePluginConfiguration(
                id=license_id,
                label=license_label,
                summary=license_summary,
                text=license_text,
            )
        )
        assert sut.dump()["licenses"] == {
            license_id: {
                "label": license_label,
                "summary": license_summary,
                "text": license_text,
            }
        }


class TestCopyrightNoticePluginConfiguration:
    def test_load(self) -> None:
        summary = "My First Summary"
        text = "My First Text"
        portable: PortableData = {
            "id": "hello-world",
            "label": "Hello, world!",
            "summary": summary,
            "text": text,
        }
        sut = CopyrightNoticePluginConfiguration.load(portable)
        assert sut.summary.localize(DEFAULT_LOCALIZER) == summary
        assert sut.text.localize(DEFAULT_LOCALIZER) == text

    def test_dump(self) -> None:
        summary = "My First Summary"
        text = "My First Text"
        sut = CopyrightNoticePluginConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=summary, text=text
        )
        portable = sut.dump()
        assert portable["summary"] == summary
        assert portable["text"] == text

    def test_summary(self) -> None:
        summary = Plain("My First Summary")
        sut = CopyrightNoticePluginConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=summary, text=DUMMY_LOCALIZABLE
        )
        assert sut.summary is summary

    def test_text(self) -> None:
        text = Plain("My First Summary")
        sut = CopyrightNoticePluginConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=DUMMY_LOCALIZABLE, text=text
        )
        assert sut.text is text


class TestLicensePluginConfiguration:
    def test_load(self) -> None:
        summary = "My First Summary"
        text = "My First Text"
        portable: PortableData = {
            "id": "hello-world",
            "label": "Hello, world!",
            "summary": summary,
            "text": text,
        }
        sut = LicensePluginConfiguration.load(portable)
        assert sut.summary.localize(DEFAULT_LOCALIZER) == summary
        assert sut.text.localize(DEFAULT_LOCALIZER) == text

    def test_dump(self) -> None:
        summary = "My First Summary"
        text = "My First Text"
        sut = LicensePluginConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=summary, text=text
        )
        portable = sut.dump()
        assert portable["summary"] == summary
        assert portable["text"] == text

    def test_summary(self) -> None:
        summary = Plain("My First Summary")
        sut = LicensePluginConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=summary, text=DUMMY_LOCALIZABLE
        )
        assert sut.summary is summary

    def test_text(self) -> None:
        text = Plain("My First Summary")
        sut = LicensePluginConfiguration(
            id="-", label=DUMMY_LOCALIZABLE, summary=DUMMY_LOCALIZABLE, text=text
        )
        assert sut.text is text
