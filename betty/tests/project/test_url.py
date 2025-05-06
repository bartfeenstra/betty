from typing import Any

import pytest
from pytest_mock import MockerFixture

from betty.ancestry import Ancestry
from betty.app import App
from betty.locale import DEFAULT_LOCALE, Localey
from betty.media_type import MediaType
from betty.media_type.media_types import HTML, JSON
from betty.model import ENTITY_TYPE_REPOSITORY, Entity
from betty.plugin.proxy import ProxyPluginRepository
from betty.plugin.static import StaticPluginRepository
from betty.project import Project
from betty.project.config import LocaleConfiguration
from betty.project.url import (
    _EntityUrlUrlGenerator,
    _LocalizedPathUrlUrlGenerator,
    _StaticPathUrlUrlGenerator,
    new_project_url_generator,
)
from betty.test_utils.model import DummyEntity


class Test_EntityUrlUrlGenerator:
    _ENTITY_ID = "E0"

    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (False, ""),
            (False, "betty-entity"),
            (False, "betty-entity://"),
            (False, "betty-entity://["),
            (False, f"betty-entity://{DummyEntity.plugin_id()}"),
            (False, f"betty-entity://{DummyEntity.plugin_id()}/"),
            (True, f"betty-entity://{DummyEntity.plugin_id()}/{_ENTITY_ID}"),
            (False, "/"),
        ],
    )
    async def test_supports(
        self,
        expected: bool,
        resource: Any,
        mocker: MockerFixture,
    ) -> None:
        m_entity_url_generator = mocker.patch("betty.project.url._EntityUrlGenerator")
        plugin_repository = StaticPluginRepository(DummyEntity)
        ancestry = Ancestry(
            entity_type_id_to_type_mapping=await plugin_repository.mapping()
        )
        sut = _EntityUrlUrlGenerator(ancestry, m_entity_url_generator)
        assert sut.supports(resource) == expected

    async def test_generate(self, mocker: MockerFixture) -> None:
        url = f"https://example.com/betty/{self._ENTITY_ID}"
        locale = "nl-NL"
        m_entity_url_generator = mocker.patch("betty.project.url._EntityUrlGenerator")
        m_entity_url_generator.generate.return_value = url
        plugin_repository = StaticPluginRepository(DummyEntity)
        entity = DummyEntity(self._ENTITY_ID)
        ancestry = Ancestry(
            entity_type_id_to_type_mapping=await plugin_repository.mapping()
        )
        ancestry.add(entity)
        sut = _EntityUrlUrlGenerator(ancestry, m_entity_url_generator)
        assert (
            sut.generate(
                f"betty-entity://{DummyEntity.plugin_id()}/{self._ENTITY_ID}",
                media_type=HTML,
                absolute=True,
                locale=locale,
            )
            == url
        )
        m_entity_url_generator.generate.assert_called_once_with(
            entity, media_type=HTML, absolute=True, locale=locale
        )


class Test_LocalizedPathUrlUrlGenerator:
    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (False, ""),
            (False, "betty"),
            (False, "betty://"),
            (False, "betty://["),
            (True, "betty://without-leading-slash/index.html"),
            (True, "betty:///with-leading-slash/index.html"),
            (False, "betty-other://without-leading-slash/index.html"),
            (False, "betty-other:///with-leading-slash/index.html"),
            (False, "/"),
        ],
    )
    async def test_supports(
        self, expected: bool, resource: Any, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await _LocalizedPathUrlUrlGenerator.new_for_project(project)
            assert sut.supports(resource) == expected

    _GENERATE_RESOURCES = [
        "betty://some/path/index.html",
        "betty:///some/path/index.html",
    ]

    @pytest.mark.parametrize(
        (
            "expected",
            "resource",
            "media_type",
            "absolute",
            "locale",
            "additional_project_locale",
        ),
        [
            *[
                (
                    "/some/path/index.html",
                    resource,
                    media_type,
                    False,
                    None,
                    None,
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
            ],
            *[
                (
                    "https://example.com/some/path/index.html",
                    resource,
                    media_type,
                    True,
                    None,
                    None,
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
            ],
            *[
                (
                    f"/{DEFAULT_LOCALE}/some/path/index.html",
                    resource,
                    media_type,
                    False,
                    None,
                    "nl-NL",
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
            ],
            *[
                (
                    "/nl-NL/some/path/index.html",
                    resource,
                    media_type,
                    False,
                    "nl-NL",
                    "nl-NL",
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
            ],
        ],
    )
    async def test_generate(
        self,
        expected: str,
        resource: str,
        media_type: MediaType,
        absolute: bool,
        locale: Localey | None,
        additional_project_locale: str | None,
        new_temporary_app: App,
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            if additional_project_locale:
                project.configuration.locales.append(
                    LocaleConfiguration(additional_project_locale)
                )
            async with project:
                sut = await _LocalizedPathUrlUrlGenerator.new_for_project(project)
                assert (
                    sut.generate(
                        resource,
                        media_type=media_type,
                        absolute=absolute,
                        locale=locale,
                    )
                    == expected
                )


class Test_StaticPathUrlUrlGenerator:
    _GENERATE_RESOURCES = [
        "betty-static://some/path/index.html",
        "betty-static:///some/path/index.html",
    ]

    @pytest.mark.parametrize(
        ("expected", "resource"),
        [
            (False, ""),
            (False, "betty-static"),
            (False, "betty-static://"),
            (False, "betty-static://["),
            (True, "betty-static://without-leading-slash/index.html"),
            (True, "betty-static:///with-leading-slash/index.html"),
            (False, "betty-static-other://without-leading-slash/index.html"),
            (False, "betty-static-other:///with-leading-slash/index.html"),
            (False, "/"),
        ],
    )
    async def test_supports(
        self, expected: bool, resource: Any, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await _StaticPathUrlUrlGenerator.new_for_project(project)
            assert sut.supports(resource) == expected

    @pytest.mark.parametrize(
        (
            "expected",
            "resource",
            "media_type",
            "absolute",
            "locale",
            "additional_project_locale",
        ),
        [
            *[
                (
                    "https://example.com/some/path/index.html",
                    resource,
                    media_type,
                    True,
                    locale,
                    additional_project_locale,
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
                for locale in [None, "nl-NL"]
                for additional_project_locale in [None, "nl-NL"]
            ],
            *[
                (
                    "/some/path/index.html",
                    resource,
                    media_type,
                    False,
                    locale,
                    additional_project_locale,
                )
                for resource in _GENERATE_RESOURCES
                for media_type in [HTML, JSON]
                for locale in [None, "nl-NL"]
                for additional_project_locale in [None, "nl-NL"]
            ],
        ],
    )
    async def test_generate(
        self,
        expected: str,
        resource: str,
        media_type: MediaType,
        absolute: bool,
        locale: Localey | None,
        additional_project_locale: str | None,
        new_temporary_app: App,
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            if additional_project_locale:
                project.configuration.locales.append(
                    LocaleConfiguration(additional_project_locale)
                )
            async with project:
                sut = await _StaticPathUrlUrlGenerator.new_for_project(project)
                assert (
                    sut.generate(
                        resource,
                        media_type=media_type,
                        absolute=absolute,
                        locale=locale,
                    )
                    == expected
                )


@pytest.mark.parametrize(
    ("expected", "resource"),
    [
        (True, DummyEntity()),
        (True, "betty://some/path/index.html"),
        (True, "betty:///some/path/index.html"),
        (True, "betty-static://some/path/index.html"),
        (True, "betty-static:///some/path/index.html"),
        (False, ""),
        (False, "/"),
        (False, "index.html"),
        (False, "example"),
        (False, "/example"),
        (False, "example/"),
        (False, "/example/"),
        (False, "example/index.html"),
        (False, "/example/index.html"),
        (False, object()),
    ],
)
async def test_new_project_url_generator__supports(
    expected: bool, resource: Any, new_temporary_app: App, mocker: MockerFixture
) -> None:
    mocker.patch(
        "betty.model.ENTITY_TYPE_REPOSITORY",
        new=ProxyPluginRepository[Entity](
            StaticPluginRepository(DummyEntity), ENTITY_TYPE_REPOSITORY
        ),
    )
    async with Project.new_temporary(new_temporary_app) as project, project:
        sut = await new_project_url_generator(project)
        assert sut.supports(resource) == expected


@pytest.mark.parametrize(
    (
        "expected",
        "clean_urls",
        "resource",
        "media_type",
        "absolute",
        "locale",
        "additional_project_locale",
    ),
    [
        # Entities
        (
            "https://example.com/dummy-entity/E0/index.html",
            False,
            DummyEntity("E0"),
            HTML,
            True,
            None,
            None,
        ),
        # betty:// URLs
        (
            "https://example.com/some/path/index.html",
            False,
            "betty:///some/path/index.html",
            HTML,
            True,
            None,
            None,
        ),
        # betty-static:// URLs
        (
            "https://example.com/some/path/index.html",
            False,
            "betty-static:///some/path/index.html",
            HTML,
            True,
            None,
            None,
        ),
    ],
)
async def test_new_project_url_generator__generate(
    expected: str,
    clean_urls: bool,
    resource: str,
    media_type: MediaType,
    absolute: bool,
    locale: Localey | None,
    additional_project_locale: str | None,
    new_temporary_app: App,
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        "betty.model.ENTITY_TYPE_REPOSITORY",
        new=ProxyPluginRepository[Entity](
            StaticPluginRepository(DummyEntity), ENTITY_TYPE_REPOSITORY
        ),
    )
    async with Project.new_temporary(new_temporary_app) as project:
        if additional_project_locale:
            project.configuration.locales.append(
                LocaleConfiguration(additional_project_locale)
            )
        project.configuration.clean_urls = clean_urls
        async with project:
            sut = await new_project_url_generator(project)
            assert (
                sut.generate(
                    resource,
                    media_type=media_type,
                    absolute=absolute,
                    locale=locale,
                )
                == expected
            )
