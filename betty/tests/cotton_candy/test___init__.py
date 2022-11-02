from typing import Dict

import pytest

from betty.app import App
from betty.config import ConfigurationError
from betty.cotton_candy import CottonCandyConfiguration
from betty.model import Entity, get_entity_type_name
from betty.project import EntityReference
from betty.typing import Void


class TestCottonCandyConfiguration:
    def test_load_with_minimal_configuration(self) -> None:
        dumped_configuration: Dict = {}
        with App():
            CottonCandyConfiguration().load(dumped_configuration)

    def test_load_without_dict_should_error(self) -> None:
        dumped_configuration = None
        with App():
            with pytest.raises(ConfigurationError):
                CottonCandyConfiguration().load(dumped_configuration)

    def test_load_should_load_theme_background_image_id(self) -> None:
        background_image_id = 'my-favorite-picture'
        dumped_configuration = {
            'background_image_id': background_image_id
        }
        configuration = CottonCandyConfiguration()
        configuration.load(dumped_configuration)
        assert background_image_id == configuration.background_image.entity_id

    def test_dump_with_minimal_configuration(self) -> None:
        sut = CottonCandyConfiguration()
        expected = Void
        assert expected == sut.dump()

    def test_dump_with_background_image_id(self) -> None:
        sut = CottonCandyConfiguration()
        background_image_id = '123'
        sut.background_image.entity_id = background_image_id
        expected = {
            'background_image_id': background_image_id,
        }
        assert expected == sut.dump()

    def test_dump_with_featured_entities(self) -> None:
        sut = CottonCandyConfiguration()
        entity_type = Entity
        entity_id = '123'
        sut.featured_entities.append(EntityReference(entity_type, entity_id))
        expected = {
            'featured_entities': [
                {
                    'entity_type': get_entity_type_name(entity_type),
                    'entity_id': entity_id,
                },
            ],
        }
        assert expected == sut.dump()
