from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from betty.ancestry import Ancestry
from betty.asset import Asset, AssetDefinition
from betty.dirs import ASSETS_DIRECTORY_PATH
from betty.extension import Extension, ExtensionDefinition
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.project import Project
from betty.project.data import ProjectConfiguration, ProjectLocale
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.project.extension import DummyExtensionOne

if TYPE_CHECKING:
    from betty.app import App


class _DummyExtension(Extension):
    # Provide an initializer without arguments so the factory can call it.
    def __init__(self):
        super().__init__()


@AssetDefinition("dummy", assets=Path(__file__).parent / "dummy" / "assets")
class _DummyAsset(Asset):
    pass


@ExtensionDefinition("dummy-a", label=DUMMY_LOCALIZABLE)
class _DummyExtensionA(_DummyExtension):
    pass


@ExtensionDefinition("dummy-b", label=DUMMY_LOCALIZABLE)
class _DummyExtensionB(_DummyExtension):
    pass


class TestProject:
    async def test_configuration(self, isolated_app: App) -> None:
        configuration = ProjectConfiguration(
            title=DUMMY_LOCALIZABLE, url="https://example.com"
        )
        async with (
            Project.new_isolated(isolated_app, configuration=configuration) as sut,
            sut,
        ):
            assert sut.configuration is configuration

    async def test_new(self, isolated_app: App, tmp_path: Path) -> None:
        configuration = ProjectConfiguration(title="Betty", url="https://example.com")
        sut = await Project.new(isolated_app, configuration, directory=tmp_path)
        assert sut.upstream is isolated_app
        assert sut.configuration is configuration
        assert sut.directory == tmp_path

    async def test_new_isolated__without_configuration(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_isolated(isolated_app):
            pass

    async def test_new_isolated__with_configuration(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        configuration = ProjectConfiguration(title="Betty", url="https://example.com")
        async with Project.new_isolated(
            isolated_app, configuration=configuration
        ) as sut:
            assert sut.configuration is configuration

    async def test_bootstrap__should_initialize_extensions(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(
            isolated_app, plugins={ExtensionDefinition: [DummyExtensionOne]}
        ) as sut:
            sut.configuration.extensions.add(DummyExtensionOne)
            async with sut:
                extensions = await sut.extensions
                extension = extensions[DummyExtensionOne]
                assert extension.bootstrapped

    async def test_extensions(self, isolated_app: App) -> None:
        async with Project.new_isolated(
            isolated_app,
            plugins={ExtensionDefinition: [DummyExtensionOne]},
        ) as sut:
            sut.configuration.extensions.add(DummyExtensionOne)
            async with sut:
                assert DummyExtensionOne in await sut.extensions

    async def test_ancestry__with___init___ancestry(self, isolated_app: App) -> None:
        ancestry = Ancestry()
        async with (
            Project.new_isolated(isolated_app, ancestry=ancestry) as sut,
            sut,
        ):
            assert sut.ancestry is ancestry

    async def test_ancestry__without___init___ancestry(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            sut.ancestry  # noqa: B018

    async def test_assets(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            assets = await sut.assets
            assert len(assets.directories) == 2

    async def test_jinja(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            await sut.jinja

    async def test_localizers(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            localizers = await sut.localizers
            assert localizers is await sut.localizers

    async def test_name__with_configuration_name(self, isolated_app: App) -> None:
        name = "hello-world"
        async with Project.new_isolated(isolated_app) as sut:
            sut.configuration.name = name
            async with sut:
                assert sut.name == name

    async def test_name__without_configuration_name(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            sut.name  # noqa: B018

    async def test_renderer(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            await sut.renderer

    async def test_url_generator(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            await sut.url_generator

    async def test_logo__with_configuration(self, isolated_app: App) -> None:
        logo = (
            ASSETS_DIRECTORY_PATH
            / "universe"
            / "public"
            / "static"
            / "betty-512x512.png"
        )
        async with Project.new_isolated(isolated_app) as sut:
            sut.configuration.logo = logo
            async with sut:
                assert sut.logo == logo

    async def test_logo__without_configuration(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            assert sut.logo.exists()

    async def test_copyright_notice(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            assert await sut.copyright_notice is await sut.copyright_notice

    async def test_license(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            assert await sut.license is await sut.license

    async def test_privatizer(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            sut.privatizer  # noqa: B018

    async def test_new_document(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            await sut.new_document()

    async def test_directory(self, isolated_app: App, tmp_path: Path) -> None:
        sut = Project(
            tmp_path,
            app=isolated_app,
            configuration=ProjectConfiguration(
                title="Betty", url="https://example.com"
            ),
        )
        assert sut.directory == tmp_path

    async def test_output_directory(self, isolated_app: App, tmp_path: Path) -> None:
        sut = Project(
            tmp_path,
            app=isolated_app,
            configuration=ProjectConfiguration(
                title="Betty", url="https://example.com"
            ),
        )
        assert tmp_path in sut.output_directory.parents

    async def test_assets_directory(self, isolated_app: App, tmp_path: Path) -> None:
        sut = Project(
            tmp_path,
            app=isolated_app,
            configuration=ProjectConfiguration(
                title="Betty", url="https://example.com"
            ),
        )
        assert tmp_path in sut.assets_directory.parents

    async def test_www_directory(self, isolated_app: App, tmp_path: Path) -> None:
        sut = Project(
            tmp_path,
            app=isolated_app,
            configuration=ProjectConfiguration(
                title="Betty", url="https://example.com"
            ),
        )
        assert tmp_path in sut.www_directory.parents

    async def test_localize_www_directory__monolingual(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = Project(
            tmp_path,
            app=isolated_app,
            configuration=ProjectConfiguration(
                title="Betty", url="https://example.com"
            ),
        )
        actual = sut.localize_www_directory(DEFAULT_LOCALE)
        assert tmp_path in actual.parents
        assert DEFAULT_LOCALE_TAG not in str(actual)

    async def test_localize_www_directory__multilingual(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = Project(
            tmp_path,
            app=isolated_app,
            configuration=ProjectConfiguration(
                title="Betty", url="https://example.com"
            ),
        )
        sut.configuration.locales.add(ProjectLocale("nl-NL"))
        actual = sut.localize_www_directory(DEFAULT_LOCALE)
        assert tmp_path in actual.parents
        assert DEFAULT_LOCALE_TAG in str(actual)
