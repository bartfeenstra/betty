from typing import Dict

import pytest

from betty.app import App
from betty.config import DumpedConfiguration
from betty.config.load import ConfigurationValidationError
from betty.cotton_candy import CottonCandyConfiguration, _ColorConfiguration
from betty.model import Entity, get_entity_type_name
from betty.project import EntityReference
from betty.tests.config.test___init__ import raises_configuration_error


class TestColorConfiguration:
    def test_hex_with_valid_value(self) -> None:
        hex_value = '#000000'
        sut = _ColorConfiguration('#ffffff')
        sut.hex = hex_value
        assert hex_value == sut.hex

    @pytest.mark.parametrize('hex_value', [
        'rgb(0,0,0)',
        'pink',
    ])
    def test_hex_with_invalid_value(self, hex_value: str) -> None:
        sut = _ColorConfiguration('#ffffff')
        with App():
            with pytest.raises(ConfigurationValidationError):
                sut.hex = hex_value

    def test_load_with_valid_hex_value(self) -> None:
        hex_value = '#000000'
        dumped_configuration = hex_value
        sut = _ColorConfiguration('#ffffff').load(dumped_configuration)
        assert hex_value == sut.hex

    @pytest.mark.parametrize('dumped_configuration', [
        False,
        123,
        'rgb(0,0,0)',
        'pink',
    ])
    def test_load_with_invalid_value(self, dumped_configuration: DumpedConfiguration) -> None:
        sut = _ColorConfiguration('#ffffff')
        with raises_configuration_error(error_type=ConfigurationValidationError):
            sut.load(dumped_configuration)

    def test_dump_with_value(self) -> None:
        hex_value = '#000000'
        assert hex_value == _ColorConfiguration(hex_value=hex_value).dump()


class CottonCandyConfigurationTestEntity(Entity):
    pass


class CottonCandyConfigurationTestEntitytest_load_with_featured_entities:
    pass


class TestCottonCandyConfiguration:
    def test_load_with_minimal_configuration(self) -> None:
        dumped_configuration: Dict = {}
        CottonCandyConfiguration().load(dumped_configuration)

    def test_load_without_dict_should_error(self) -> None:
        dumped_configuration = None
        with raises_configuration_error(error_type=ConfigurationValidationError):
            CottonCandyConfiguration().load(dumped_configuration)

    def test_load_with_featured_entities(self) -> None:
        entity_type = CottonCandyConfigurationTestEntity
        entity_id = '123'
        dumped_configuration: DumpedConfiguration = {
            'featured_entities': [
                {
                    'entity_type': get_entity_type_name(entity_type),
                    'entity_id': entity_id,
                },
            ],
        }
        sut = CottonCandyConfiguration.load(dumped_configuration)
        assert entity_type == sut.featured_entities[0].entity_type
        assert entity_id == sut.featured_entities[0].entity_id

    def test_load_with_primary_inactive_color(self) -> None:
        hex_value = '#000000'
        dumped_configuration: DumpedConfiguration = {
            'primary_inactive_color': hex_value,
        }
        sut = CottonCandyConfiguration.load(dumped_configuration)
        assert hex_value == sut.primary_inactive_color.hex

    def test_load_with_primary_active_color(self) -> None:
        hex_value = '#000000'
        dumped_configuration: DumpedConfiguration = {
            'primary_active_color': hex_value,
        }
        sut = CottonCandyConfiguration.load(dumped_configuration)
        assert hex_value == sut.primary_active_color.hex

    def test_load_with_link_inactive_color(self) -> None:
        hex_value = '#000000'
        dumped_configuration: DumpedConfiguration = {
            'link_inactive_color': hex_value,
        }
        sut = CottonCandyConfiguration.load(dumped_configuration)
        assert hex_value == sut.link_inactive_color.hex

    def test_load_with_link_active_color(self) -> None:
        hex_value = '#000000'
        dumped_configuration: DumpedConfiguration = {
            'link_active_color': hex_value,
        }
        sut = CottonCandyConfiguration.load(dumped_configuration)
        assert hex_value == sut.link_active_color.hex

    def test_dump_with_minimal_configuration(self) -> None:
        sut = CottonCandyConfiguration()
        expected = {
            'primary_inactive_color': CottonCandyConfiguration.DEFAULT_PRIMARY_INACTIVE_COLOR,
            'primary_active_color': CottonCandyConfiguration.DEFAULT_PRIMARY_ACTIVE_COLOR,
            'link_inactive_color': CottonCandyConfiguration.DEFAULT_LINK_INACTIVE_COLOR,
            'link_active_color': CottonCandyConfiguration.DEFAULT_LINK_ACTIVE_COLOR,
        }
        assert expected == sut.dump()

    def test_dump_with_featured_entities(self) -> None:
        sut = CottonCandyConfiguration()
        entity_type = CottonCandyConfigurationTestEntity
        entity_id = '123'
        sut.featured_entities.append(EntityReference(entity_type, entity_id))
        expected = [
            {
                'entity_type': get_entity_type_name(entity_type),
                'entity_id': entity_id,
            },
        ]
        assert expected == sut.dump()['featured_entities']  # type: ignore

    def test_dump_with_primary_inactive_color(self) -> None:
        hex_value = '#000000'
        sut = CottonCandyConfiguration()
        sut.primary_inactive_color.hex = hex_value
        assert hex_value == sut.dump()['primary_inactive_color']  # type: ignore

    def test_dump_with_primary_active_color(self) -> None:
        hex_value = '#000000'
        sut = CottonCandyConfiguration()
        sut.primary_active_color.hex = hex_value
        assert hex_value == sut.dump()['primary_active_color']  # type: ignore

    def test_dump_with_link_inactive_color(self) -> None:
        hex_value = '#000000'
        sut = CottonCandyConfiguration()
        sut.link_inactive_color.hex = hex_value
        assert hex_value == sut.dump()['link_inactive_color']  # type: ignore

    def test_dump_with_link_active_color(self) -> None:
        hex_value = '#000000'
        sut = CottonCandyConfiguration()
        sut.link_active_color.hex = hex_value
        assert hex_value == sut.dump()['link_active_color']  # type: ignore
