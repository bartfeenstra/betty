from typing import Any

import pytest

from betty.entity.collection.pool import EntityPool
from betty.locale import default_locale, default_locale_tag
from betty.media_types.html import HTML
from betty.test_utils.entity import DummyEntityOne
from betty.url_generators.entity import EntityUrlGenerator
from betty.url_generators.entity_url import EntityUrlUrlGenerator
from betty.url_generators.path import PathUrlGenerator


class TestEntityUrlUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (False, ""),
            (False, "betty-entity"),
            (False, "betty-entity://"),
            (False, "betty-entity://["),
            (False, f"betty-entity://{DummyEntityOne.plugin().id}"),
            (False, f"betty-entity://{DummyEntityOne.plugin().id}/"),
            (True, f"betty-entity://{DummyEntityOne.plugin().id}/my-first-entity"),
            (False, "/"),
        ],
    )
    async def test_supports(self, expected: bool, resource: Any) -> None:
        ancestry = EntityPool()
        sut = EntityUrlUrlGenerator(
            ancestry,
            EntityUrlGenerator(
                PathUrlGenerator(
                    base_url="https://example.com",
                    root_path="/",
                    locales_to_slugs={
                        default_locale: default_locale_tag,
                    },
                    clean_urls=True,
                )
            ),
        )
        assert sut.supports(resource) == expected

    async def test_generate(self) -> None:
        fragment = "my-first-fragment"
        locale = "nl-NL"
        query = {"my_first_query": "my first value"}
        entity = DummyEntityOne()
        ancestry = EntityPool()
        ancestry.add(entity)
        sut = EntityUrlUrlGenerator(
            ancestry,
            EntityUrlGenerator(
                PathUrlGenerator(
                    base_url="https://example.com",
                    root_path="/",
                    locales_to_slugs={
                        default_locale: default_locale_tag,
                    },
                    clean_urls=True,
                )
            ),
        )
        assert (
            sut.generate(
                f"betty-entity://{DummyEntityOne.plugin().id}/{entity.id}",
                absolute=True,
                fragment=fragment,
                locale=locale,
                media_type=HTML,
                query=query,
            )
            == f"https://example.com/dummy-one/{entity.id}?my_first_query=my+first+value#my-first-fragment"
        )
