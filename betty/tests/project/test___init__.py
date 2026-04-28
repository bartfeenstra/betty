from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from babel import Locale

from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.entity import EntityDefinition
from betty.entity.collection.pool import EntityPool
from betty.exception import HumanFacingException
from betty.extension import Extension, ExtensionDefinition
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.project import Project, ProjectLocale
from betty.project.data import ProjectConfiguration
from betty.test_utils.data import DataTestBase
from betty.test_utils.entity import DummyEntityOne
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.project.extension import DummyExtensionOne

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App
    from betty.test_utils.conftest import IsolatedAppFactory, IsolatedProjectFactory


class _DummyExtension(Extension):
    pass


@ExtensionDefinition("dummy-a", label=DUMMY_LOCALIZABLE)
class _DummyExtensionA(_DummyExtension):
    pass


@ExtensionDefinition("dummy-b", label=DUMMY_LOCALIZABLE)
class _DummyExtensionB(_DummyExtension):
    pass


class TestProject:
    async def test_new(self, isolated_app: App, tmp_path: Path) -> None:
        configuration = ProjectConfiguration(title="Betty", url="https://example.com")
        sut = await Project.new(isolated_app, configuration, directory=tmp_path)
        assert sut.upstream is isolated_app
        assert sut.directory == tmp_path

    async def test_new_isolated__without_app(self) -> None:
        async with Project.new_isolated() as sut:
            assert sut.upstream

    async def test_new_isolated(self, isolated_app: App) -> None:
        async with Project.new_isolated(app=isolated_app) as sut:
            assert sut.upstream is isolated_app

    async def test_bootstrap__should_initialize_extensions(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            plugins={ExtensionDefinition: [DummyExtensionOne]},
            extensions=[DummyExtensionOne],
        ) as sut:
            extension = await sut.extensions[DummyExtensionOne]
            assert extension.bootstrapped

    async def test_extensions(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            plugins={ExtensionDefinition: [DummyExtensionOne]},
            extensions=[DummyExtensionOne],
        ) as sut:
            assert DummyExtensionOne in sut.extensions

    async def test_ancestry__with___init___ancestry(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        ancestry = EntityPool()
        async with isolated_project_factory(ancestry=ancestry) as sut:
            assert sut.ancestry is ancestry

    async def test_ancestry__without___init___ancestry(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            sut.ancestry  # noqa: B018

    async def test_assets(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            assert len(sut.asset_directories.directories) == 2

    async def test_jinja(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            await sut.jinja

    async def test_localizers(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            localizers = await sut.localizers
            assert localizers is await sut.localizers

    async def test_name(self, isolated_project_factory: IsolatedProjectFactory) -> None:
        name = "hello-world"
        async with isolated_project_factory(name=name) as sut:
            assert sut.name == name

    async def test_name__default(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            sut.name  # noqa: B018

    async def test_renderer(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            await sut.renderer

    async def test_url_generator(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            await sut.url_generator

    async def test_logo(self, isolated_project_factory: IsolatedProjectFactory) -> None:
        logo = ASSETS_DIRECTORY_PATH / "app" / "public" / "static" / "betty-256x256.png"
        async with isolated_project_factory(logo=logo) as sut:
            assert sut.logo == logo

    async def test_logo__default(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            assert sut.logo.exists()

    async def test_copyright_notice(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            assert await sut.copyright_notice is await sut.copyright_notice

    async def test_license(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            assert await sut.license is await sut.license

    async def test_privatizer(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            sut.privatizer  # noqa: B018

    async def test_new_document(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory() as sut:
            await sut.new_document()

    async def test_directory(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> None:
        async with isolated_project_factory(directory=tmp_path) as sut:
            assert sut.directory == tmp_path

    async def test_output_directory(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> None:
        async with isolated_project_factory(directory=tmp_path) as sut:
            assert tmp_path in sut.output_directory.parents

    async def test_assets_directory(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> None:
        async with isolated_project_factory(directory=tmp_path) as sut:
            assert tmp_path in sut.assets_directory.parents

    async def test_www_directory(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> None:
        async with isolated_project_factory(directory=tmp_path) as sut:
            assert tmp_path in sut.www_directory.parents

    async def test_localize_www_directory__monolingual(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> None:
        async with isolated_project_factory(directory=tmp_path) as sut:
            actual = sut.localize_www_directory(DEFAULT_LOCALE)
            assert tmp_path in actual.parents
            assert DEFAULT_LOCALE_TAG not in str(actual)

    async def test_localize_www_directory__multilingual(
        self, isolated_project_factory: IsolatedProjectFactory, tmp_path: Path
    ) -> None:
        async with isolated_project_factory(locales=[DEFAULT_LOCALE, "nl-NL"]) as sut:
            actual = sut.localize_www_directory(DEFAULT_LOCALE)
            assert sut.directory in actual.parents
            assert DEFAULT_LOCALE_TAG in str(actual)

    async def test_author(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        author = "Bart"
        async with isolated_project_factory(author=author) as project:
            assert project.author is not None
            assert project.author.localize(DEFAULT_LOCALIZER) == author

    async def test_base_url(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            url="https://betty.example.com:747/my-first-site"
        ) as sut:
            assert sut.base_url == "https://betty.example.com:747"

    async def test_clean_urls(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(clean_urls=True) as sut:
            assert sut.clean_urls

    async def test_debug(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(debug=True) as sut:
            assert sut.debug

    async def test_default_locale(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(locales=["nl-NL", "en-US"]) as sut:
            assert str(sut.default_locale.locale) == "nl_NL"

    async def test_generate_entity_list_html(
        self,
        isolated_app_factory: IsolatedAppFactory,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_app_factory(
                plugins={
                    EntityDefinition: [DummyEntityOne],
                }
            ) as app,
            isolated_project_factory(
                app=app, generate_entity_list_html=[DummyEntityOne]
            ) as sut,
        ):
            assert list(await sut.generate_entity_list_html) == [
                DummyEntityOne.plugin()
            ]

    async def test_lifetime_threshold(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        lifetime_threshold = 999
        async with isolated_project_factory(
            lifetime_threshold=lifetime_threshold
        ) as sut:
            assert sut.lifetime_threshold == lifetime_threshold

    async def test_locales(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(locales=["nl-NL"]) as sut:
            assert len(sut.locales) == 1
            assert str(next(iter(sut.locales)).locale) == "nl_NL"

    async def test_multilingual__without_multilingual(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(locales=["nl-NL"]) as sut:
            assert not sut.multilingual

    async def test_multilingual__with_multilingual(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(locales=["nl-NL", "en-US"]) as sut:
            assert sut.multilingual

    async def test_root_path(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            url="https://betty.example.com:747/my-first-site"
        ) as sut:
            assert sut.root_path == "/my-first-site"

    async def test_title(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        title = "My First Betty Site"
        async with isolated_project_factory(title=title) as sut:
            assert sut.title.localize(DEFAULT_LOCALIZER) == title

    async def test_url(self, isolated_project_factory: IsolatedProjectFactory) -> None:
        url = "https://betty.example.com"
        async with isolated_project_factory(url=url) as sut:
            assert sut.url == url


class TestProjectLocale(DataTestBase[ProjectLocale]):
    sut_cls = ProjectLocale

    def test___init____with_invalid_alias(self) -> None:
        alias = "nl/NL"
        with pytest.raises(HumanFacingException):
            ProjectLocale("nl-NL", alias=alias)

    def test_locale(self) -> None:
        locale = Locale("nl")
        sut = ProjectLocale(locale)
        assert sut.locale is locale

    def test_alias(self) -> None:
        alias = "nl"
        sut = ProjectLocale(DEFAULT_LOCALE, alias=alias)
        assert sut.alias == alias

    def test_slug__without_alias(self) -> None:
        locale = "nl-NL"
        sut = ProjectLocale(locale)
        assert sut.slug == locale

    def test_slug__with_alias(self) -> None:
        alias = "my-first-locale"
        sut = ProjectLocale("nl-NL", alias=alias)
        assert sut.slug == alias
