from typing import Any

import pytest

from betty.entity import Entity, EntityDefinition
from betty.locale import default_locale, default_locale_tag
from betty.media_types.html import HTML
from betty.test_utils.entity import DummyEntityOne
from betty.url_generators.entity_type import EntityTypeUrlGenerator
from betty.url_generators.path import PathUrlGenerator


class TestEntityTypeUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (True, DummyEntityOne),
            (True, DummyEntityOne.plugin()),
            (False, EntityDefinition),
            (False, "/"),
            (False, object()),
        ],
    )
    def test_supports(self, expected: bool, resource: Any) -> None:
        sut = EntityTypeUrlGenerator(
            PathUrlGenerator(
                base_url="https://example.com",
                root_path="/",
                locales_to_slugs={
                    default_locale: default_locale_tag,
                },
                clean_urls=True,
            )
        )
        assert sut.supports(resource) is expected

    @pytest.mark.parametrize(
        ("expected", "entity_type"),
        [
            ("/dummy-one", DummyEntityOne),
            ("/dummy-one", DummyEntityOne.plugin()),
        ],
    )
    def test_generate(
        self, expected: str, entity_type: EntityDefinition | type[Entity]
    ) -> None:
        sut = EntityTypeUrlGenerator(
            PathUrlGenerator(
                base_url="https://example.com",
                root_path="/",
                locales_to_slugs={
                    default_locale: default_locale_tag,
                },
                clean_urls=True,
            )
        )
        assert sut.generate(entity_type, media_type=HTML) == expected
