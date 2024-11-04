from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Self, Sequence

import pytest
from typing_extensions import override

import betty.ancestry.event
import betty.ancestry.person
import betty.ancestry.place
from betty.ancestry import Ancestry
from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.assertion.error import AssertionFailed
from betty.json.schema import JsonSchemaSchema
from betty.plugin import CyclicDependencyError
from betty.plugin.config import PluginConfiguration, PluginInstanceConfiguration
from betty.plugin.static import StaticPluginRepository
from betty.project import (
    Project,
    ProjectEvent,
    ProjectSchema,
    ProjectExtensions,
    ProjectContext,
)
from betty.project.config import (
    CopyrightNoticeConfiguration,
    LicenseConfiguration,
    ProjectConfiguration,
    EntityTypeConfiguration,
)
from betty.project.factory import ProjectDependentFactory
from betty.test_utils.config import DummyConfiguration
from betty.test_utils.json.schema import SchemaTestBase
from betty.test_utils.model import DummyEntity
from betty.test_utils.project.extension import (
    DummyExtension,
    DummyConfigurableExtension,
)

if TYPE_CHECKING:
    from betty.project.extension import Extension
    from betty.plugin import PluginIdentifier
    from betty.json.schema import Schema
    from collections.abc import MutableSequence
    from pytest_mock import MockerFixture
    from betty.serde.dump import Dump


class _CyclicDependencyOneExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {_CyclicDependencyTwoExtension}


class _CyclicDependencyTwoExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {_CyclicDependencyOneExtension}


class _DependsOnNonConfigurableExtensionExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {DummyExtension}


class _AlsoDependsOnNonConfigurableExtensionExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {DummyExtension}


class _DependsOnNonConfigurableExtensionExtensionExtension(DummyExtension):
    @classmethod
    def depends_on(cls) -> set[PluginIdentifier[Extension]]:
        return {_DependsOnNonConfigurableExtensionExtension}


class _ComesBeforeNonConfigurableExtensionExtension(DummyExtension):
    @classmethod
    def comes_before(cls) -> set[PluginIdentifier[Extension]]:
        return {DummyExtension}


class _ComesAfterNonConfigurableExtensionExtension(DummyExtension):
    @classmethod
    def comes_after(cls) -> set[PluginIdentifier[Extension]]:
        return {DummyExtension}


class _DummyExtensionWithAssetsDirectory(DummyExtension):
    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / cls.plugin_id() / "assets"


class TestProject:
    @pytest.fixture
    def _extensions(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "betty.project.extension.EXTENSION_REPOSITORY",
            new=StaticPluginRepository(
                DummyExtension,
                DummyConfigurableExtension,
                _AlsoDependsOnNonConfigurableExtensionExtension,
                _ComesBeforeNonConfigurableExtensionExtension,
                _ComesAfterNonConfigurableExtensionExtension,
                _DependsOnNonConfigurableExtensionExtension,
                _DependsOnNonConfigurableExtensionExtensionExtension,
                _DummyExtensionWithAssetsDirectory,
                _CyclicDependencyOneExtension,
                _CyclicDependencyTwoExtension,
            ),
        )

    async def test_new_without_ancestry(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        await Project.new(
            new_temporary_app,
            configuration=await ProjectConfiguration.new(tmp_path / "betty.json"),
        )

    async def test_new_with_ancestry(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        ancestry = await Ancestry.new()
        sut = await Project.new(
            new_temporary_app,
            configuration=await ProjectConfiguration.new(tmp_path / "betty.json"),
            ancestry=ancestry,
        )
        assert sut.ancestry is ancestry

    async def test_new_temporary_without_configuration(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(new_temporary_app):
            pass

    async def test_new_temporary_with_configuration(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        configuration = await ProjectConfiguration.new(tmp_path / "betty.json")
        async with Project.new_temporary(
            new_temporary_app, configuration=configuration
        ) as sut:
            assert sut.configuration is configuration

    @pytest.mark.usefixtures("_extensions")
    async def test_bootstrap_should_initialize_extensions(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(DummyExtension)
            async with sut:
                extensions = await sut.extensions
                extension = extensions[DummyExtension.plugin_id()]
                assert extension._bootstrapped

    async def test_bootstrap_should_validate_entity_type_configuration(
        self, mocker: MockerFixture, new_temporary_app: App
    ) -> None:
        plugin = DummyEntity
        mocker.patch(
            "betty.model.ENTITY_TYPE_REPOSITORY", new=StaticPluginRepository(plugin)
        )
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.entity_types.replace(
                EntityTypeConfiguration(plugin, generate_html_list=True)
            )
            with pytest.raises(AssertionFailed):
                async with sut:
                    pass

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_one_extension(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(DummyExtension)
            async with sut:
                extensions = await sut.extensions
                extension = extensions[DummyExtension.plugin_id()]
                assert isinstance(extension, DummyExtension)

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_one_configurable_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            value = "Hello, world!"
            sut.configuration.extensions.append(
                PluginInstanceConfiguration(
                    DummyConfigurableExtension,
                    configuration=DummyConfiguration(value=value),
                )
            )
            async with sut:
                extensions = await sut.extensions
                extension = extensions[DummyConfigurableExtension]
                assert isinstance(extension, DummyConfigurableExtension)
                assert extension.configuration.value == value

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_one_extension_with_single_chained_dependency(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(
                _DependsOnNonConfigurableExtensionExtensionExtension
            )
            async with sut:
                extensions = [list(batch) for batch in await sut.extensions]
                assert len(extensions) == 3
                assert len(extensions[0]) == 1
                assert isinstance(extensions[0][0], DummyExtension)
                assert len(extensions[1]) == 1
                assert isinstance(
                    extensions[1][0], _DependsOnNonConfigurableExtensionExtension
                )
                assert len(extensions[2]) == 1
                assert isinstance(
                    extensions[2][0],
                    _DependsOnNonConfigurableExtensionExtensionExtension,
                )

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_multiple_extensions_with_duplicate_dependencies(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(
                _DependsOnNonConfigurableExtensionExtension,
                _AlsoDependsOnNonConfigurableExtensionExtension,
            )
            async with sut:
                extensions = [list(batch) for batch in await sut.extensions]
                assert len(extensions) == 2
                assert len(extensions[0]) == 1
                assert isinstance(extensions[0][0], DummyExtension)
                assert len(extensions[1]) == 2
                assert isinstance(
                    extensions[1][0], _AlsoDependsOnNonConfigurableExtensionExtension
                )
                assert isinstance(
                    extensions[1][1], _DependsOnNonConfigurableExtensionExtension
                )

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_multiple_extensions_with_cyclic_dependencies(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(_CyclicDependencyOneExtension)
            with pytest.raises(CyclicDependencyError):  # noqa PT012
                async with sut:
                    pass  # pragma: no cover

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_comes_before_with_other_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(
                DummyExtension, _ComesBeforeNonConfigurableExtensionExtension
            )
            async with sut:
                extensions = [list(batch) for batch in await sut.extensions]
                assert len(extensions) == 2
                assert len(extensions[0]) == 1
                assert isinstance(
                    extensions[0][0], _ComesBeforeNonConfigurableExtensionExtension
                )
                assert len(extensions[1]) == 1
                assert isinstance(extensions[1][0], DummyExtension)

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_comes_before_without_other_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(
                _ComesBeforeNonConfigurableExtensionExtension
            )
            async with sut:
                extensions = [list(batch) for batch in await sut.extensions]
                assert len(extensions) == 1
                assert len(extensions[0]) == 1
                assert isinstance(
                    extensions[0][0], _ComesBeforeNonConfigurableExtensionExtension
                )

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_comes_after_with_other_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(
                _ComesAfterNonConfigurableExtensionExtension, DummyExtension
            )
            async with sut:
                extensions = [list(batch) for batch in await sut.extensions]
                assert len(extensions) == 2
                assert len(extensions[0]) == 1
                assert isinstance(extensions[0][0], DummyExtension)
                assert len(extensions[1]) == 1
                assert isinstance(
                    extensions[1][0], _ComesAfterNonConfigurableExtensionExtension
                )

    @pytest.mark.usefixtures("_extensions")
    async def test_extensions_with_comes_after_without_other_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(
                _ComesAfterNonConfigurableExtensionExtension
            )
            async with sut:
                extensions = [list(batch) for batch in await sut.extensions]
                assert len(extensions) == 1
                assert len(extensions[0]) == 1
                assert isinstance(
                    extensions[0][0], _ComesAfterNonConfigurableExtensionExtension
                )

    async def test_ancestry_with___init___ancestry(
        self, new_temporary_app: App
    ) -> None:
        ancestry = await Ancestry.new()
        async with (
            Project.new_temporary(new_temporary_app, ancestry=ancestry) as sut,
            sut,
        ):
            assert sut.ancestry is ancestry

    async def test_ancestry_without___init___ancestry(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.ancestry  # noqa B018

    async def test_app(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assert sut.app is new_temporary_app

    async def test_assets_without_extensions(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assets = await sut.assets
            assert len(assets.assets_directory_paths) == 2

    @pytest.mark.usefixtures("_extensions")
    async def test_assets_with_extension_without_assets_directory(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(DummyExtension)
            async with sut:
                assets = await sut.assets
                assert len(assets.assets_directory_paths) == 2

    @pytest.mark.usefixtures("_extensions")
    async def test_assets_with_extension_with_assets_directory(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.extensions.enable(_DummyExtensionWithAssetsDirectory)
            async with sut:
                assets = await sut.assets
                assert len(assets.assets_directory_paths) == 3

    async def test_event_dispatcher(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.event_dispatcher  # noqa B018

    async def test_jinja2_environment(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            await sut.jinja2_environment

    async def test_localizers(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            localizers = await sut.localizers
            assert len(list(localizers.locales)) > 0

    async def test_name_with_configuration_name(self, new_temporary_app: App) -> None:
        name = "hello-world"
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.name = name
            async with sut:
                assert sut.name == name

    async def test_name_without_configuration_name(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            sut.name  # noqa B018

    async def test_renderer(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            await sut.renderer

    async def test_static_url_generator(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            await sut.static_url_generator

    async def test_localized_url_generator(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            await sut.localized_url_generator

    async def test_new_target(self, new_temporary_app: App) -> None:
        class Dependent:
            pass

        async with Project.new_temporary(new_temporary_app) as sut, sut:
            await sut.new_target(Dependent)

    async def test_new_with_project_dependent_factory(
        self, new_temporary_app: App
    ) -> None:
        class Dependent(ProjectDependentFactory):
            def __init__(self, project: Project):
                self.project = project

            @classmethod
            async def new_for_project(cls, project: Project) -> Self:
                return cls(project)

        async with Project.new_temporary(new_temporary_app) as sut, sut:
            dependent = await sut.new_target(Dependent)
            assert dependent.project is sut

    async def test_new_with_app_dependent_factory(self, new_temporary_app: App) -> None:
        class Dependent(AppDependentFactory):
            def __init__(self, app: App):
                self.app = app

            @override
            @classmethod
            async def new_for_app(cls, app: App) -> Self:
                return cls(app)

        async with Project.new_temporary(new_temporary_app) as sut, sut:
            dependent = await sut.new_target(Dependent)
            assert dependent.app is new_temporary_app

    async def test_logo_with_configuration(
        self, new_temporary_app: App, tmp_path: Path
    ) -> None:
        logo = tmp_path / "logo.png"
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.logo = logo
            async with sut:
                assert sut.logo == logo

    async def test_logo_without_configuration(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assert sut.logo.exists()

    async def test_copyright_notice(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assert await sut.copyright_notice is await sut.copyright_notice

    async def test_copyright_notice_repository(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.copyright_notices.append(
                CopyrightNoticeConfiguration("foo", "Foo", summary="", text="")
            )
            async with sut:
                assert await sut.copyright_notice_repository.get("foo")

    async def test_license(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assert await sut.license is await sut.license

    async def test_license_repository(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.licenses.append(
                LicenseConfiguration("foo", "Foo", summary="", text="")
            )
            async with sut:
                licenses = await sut.license_repository
                assert await licenses.get("foo")

    async def test_event_type_repository(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.event_types.append(PluginConfiguration("foo", "Foo"))
            async with sut:
                assert await sut.event_type_repository.get("foo")

    async def test_place_type_repository(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.place_types.append(PluginConfiguration("foo", "Foo"))
            async with sut:
                assert await sut.place_type_repository.get("foo")

    async def test_presence_role_repository(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.presence_roles.append(PluginConfiguration("foo", "Foo"))
            async with sut:
                assert await sut.presence_role_repository.get("foo")

    async def test_gender_repository(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut:
            sut.configuration.genders.append(PluginConfiguration("foo", "Foo"))
            async with sut:
                assert await sut.gender_repository.get("foo")

    async def test_entity_type_repository(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assert await sut.entity_type_repository.get("person")

    async def test_extension_repository(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as sut, sut:
            assert await sut.extension_repository.get("cotton-candy")


class TestProjectContext:
    async def test_project(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = ProjectContext(project)
            assert sut.project is project


class TestProjectEvent:
    async def test_project(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = ProjectEvent(ProjectContext(project))
            assert sut.project is project

    async def test_job_context(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            job_context = ProjectContext(project)
            sut = ProjectEvent(job_context)
            assert sut.job_context is job_context


class TestProjectSchema(SchemaTestBase):
    @override
    async def get_sut_instances(
        self,
    ) -> Sequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]]:
        schemas: MutableSequence[tuple[Schema, Sequence[Dump], Sequence[Dump]]] = []
        for url in (
            "http://example.com",
            "https://example.com",
            "https://example.com/root-path",
        ):
            for clean_urls in (True, False):
                async with (
                    App.new_temporary() as app,
                    app,
                    Project.new_temporary(app) as project,
                ):
                    project.configuration.url = url
                    project.configuration.clean_urls = clean_urls
                    async with project:
                        schemas.append(
                            (
                                await ProjectSchema.new_for_project(project),
                                [
                                    await betty.ancestry.person.Person().dump_linked_data(
                                        project
                                    ),
                                    await betty.ancestry.place.Place().dump_linked_data(
                                        project
                                    ),
                                    await betty.ancestry.event.Event().dump_linked_data(
                                        project
                                    ),
                                ],
                                [],
                            )
                        )
        return schemas

    @pytest.mark.parametrize(
        "clean_urls",
        [
            True,
            False,
        ],
    )
    async def test_new(self, clean_urls: bool, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = await ProjectSchema.new_for_project(project)
        json_schema = await JsonSchemaSchema.new()
        json_schema.validate(sut.schema)

    async def test_def_url(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            def_name = "myFirstDefinition"
            assert def_name in await ProjectSchema.def_url(project, def_name)

    async def test_url(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            assert "http" in await ProjectSchema.url(project)

    async def test_www_path(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            assert str(ProjectSchema.www_path(project))


class TestProjectExtensions:
    async def test___contains___without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert DummyExtension not in sut

    async def test___contains___with_unknown_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = ProjectExtensions([[DummyExtension(project)]])
            assert DummyConfigurableExtension not in sut

    async def test___contains___with_known_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = ProjectExtensions([[DummyExtension(project)]])
            assert DummyExtension in sut

    async def test___getitem___without_extensions(self) -> None:
        sut = ProjectExtensions([])
        with pytest.raises(KeyError):
            sut[DummyExtension]

    async def test___getitem___with_unknown_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = ProjectExtensions([[DummyExtension(project)]])
            with pytest.raises(KeyError):
                sut[DummyConfigurableExtension]

    async def test___getitem___with_known_extension(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            sut = ProjectExtensions([[DummyExtension(project)]])
            sut[DummyExtension]

    async def test___iter___without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert list(iter(sut)) == []

    async def test___iter___with_extensions_in_a_single_batch(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            extension_one = DummyExtension(project)
            extension_two = await DummyConfigurableExtension.new_for_project(project)
            sut = ProjectExtensions([[extension_one, extension_two]])
            actual = [list(batch) for batch in iter(sut)]
            assert len(actual) == 1
            assert len(actual[0]) == 2
            assert actual[0][0] is extension_one
            assert actual[0][1] is extension_two

    async def test___iter___with_extensions_in_multiple_batches(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            extension_one = DummyExtension(project)
            extension_two = await DummyConfigurableExtension.new_for_project(project)
            sut = ProjectExtensions([[extension_one], [extension_two]])
            actual = [list(batch) for batch in iter(sut)]
            assert len(actual) == 2
            assert len(actual[0]) == 1
            assert len(actual[1]) == 1
            assert actual[0][0] is extension_one
            assert actual[1][0] is extension_two

    async def test_flatten_without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert list(sut.flatten()) == []

    async def test_flatten_with_extensions_in_a_single_batch(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            extension_one = DummyExtension(project)
            extension_two = await DummyConfigurableExtension.new_for_project(project)
            sut = ProjectExtensions([[extension_one, extension_two]])
            actual = list(sut.flatten())
            assert len(actual) == 2
            assert actual[0] is extension_one
            assert actual[1] is extension_two

    async def test_flatten_with_extensions_in_multiple_batches(
        self, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project, project:
            extension_one = DummyExtension(project)
            extension_two = await DummyConfigurableExtension.new_for_project(project)
            sut = ProjectExtensions([[extension_one], [extension_two]])
            actual = list(sut.flatten())
            assert len(actual) == 2
            assert actual[0] is extension_one
            assert actual[1] is extension_two
