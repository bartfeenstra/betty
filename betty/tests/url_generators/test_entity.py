from typing import Any

import pytest

from betty.locale import default_locale, default_locale_tag
from betty.media_types.html import HTML
from betty.test_utils.entity import DummyEntityOne
from betty.url_generators.entity import EntityUrlGenerator
from betty.url_generators.path import PathUrlGenerator


class TestEntityUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (True, DummyEntityOne()),
            (False, DummyEntityOne),
            (False, "/"),
            (False, object()),
        ],
    )
    def test_supports(self, expected: bool, resource: Any) -> None:
        sut = EntityUrlGenerator(
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

    def test_generate(self) -> None:
        sut = EntityUrlGenerator(
            PathUrlGenerator(
                base_url="https://example.com",
                root_path="/",
                locales_to_slugs={
                    default_locale: default_locale_tag,
                },
                clean_urls=True,
            )
        )
        assert (
            sut.generate(DummyEntityOne(id="my-first-dummy"), media_type=HTML)
            == "/dummy-one/my-first-dummy"
        )
