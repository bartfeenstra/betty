from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Self

import pytest
from typing_extensions import override

import betty.ancestry.event
import betty.ancestry.person
import betty.ancestry.place
from betty.ancestry import Ancestry
from betty.app.factory import AppDependentFactory
from betty.exception import HumanFacingException
from betty.json.schema import JsonSchemaSchema
from betty.locale.localizable import Plain
from betty.model import EntityDefinition
from betty.project import Project, ProjectContext, ProjectExtensions, ProjectSchema
from betty.project.config import EntityTypeConfiguration, ProjectConfiguration
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.factory import ProjectDependentFactory
from betty.requirement import Requirement, RequirementError, StaticRequirement
from betty.test_utils.json.schema import SchemaTestBase, SchemaTestBaseSut
from betty.test_utils.model import DummyNonPublicFacingEntityOne
from betty.test_utils.plugin import DummyPluginDefinition
from betty.test_utils.project.extension import (
    DummyConfigurableExtension,
    DummyExtension,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from betty.app import App


@ExtensionDefinition(
    id="dummy-with-assets-directory",
    label=Plain(""),
    assets_directory_path=Path(__file__).parent
    / "dummy-with-assets-directory"
    / "assets",
)
class _DummyExtensionWithAssetsDirectory(Extension):
    pass


@ExtensionDefinition(
    id="dummy-unmet-requirement",
    label=Plain(""),
)
class _DummyExtensionWithUnmetRequirement(Extension):
    @override
    @classmethod
    async def requirement(cls, *, app: App) -> Requirement:
        return StaticRequirement(Plain(""))


@ExtensionDefinition(
    id="dummy-a",
    label=Plain(""),
)
class _DummyExtensionA(Extension):
    pass


@ExtensionDefinition(
    id="dummy-b",
    label=Plain(""),
)
class _DummyExtensionB(Extension):
    pass


class TestProject:
    async def test_plugins(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            await sut.plugins(DummyPluginDefinition)

    async def test_new__without_ancestry(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        Project(
            temporary_app,
            configuration=ProjectConfiguration(tmp_path / "betty.json"),
        )

    async def test_new__with_ancestry(self, temporary_app: App, tmp_path: Path) -> None:
        ancestry = Ancestry()
        sut = Project(
            temporary_app,
            configuration=ProjectConfiguration(tmp_path / "betty.json"),
            ancestry=ancestry,
        )
        assert sut.ancestry is ancestry

    async def test_new_temporary__without_configuration(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_temporary(temporary_app):
            pass

    async def test_new_temporary__with_configuration(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        configuration = ProjectConfiguration(tmp_path / "betty.json")
        async with Project.new_temporary(
            temporary_app, configuration=configuration
        ) as sut:
            assert sut.configuration is configuration

    async def test_bootstrap__should_initialize_extensions(
        self, temporary_app: App
    ) -> None:
        with ExtensionDefinition.type.override_discovery(DummyExtension.plugin):
            async with Project.new_temporary(temporary_app) as sut:
                sut.configuration.extensions.enable(DummyExtension)
                async with sut:
                    extensions = await sut.extensions
                    extension = extensions[DummyExtension]
                    assert extension.bootstrapped

    async def test_bootstrap__should_validate_entity_type_configuration(
        self, temporary_app: App
    ) -> None:
        with EntityDefinition.type.override_discovery(
            DummyNonPublicFacingEntityOne.plugin
        ):
            async with Project.new_temporary(temporary_app) as sut:
                sut.configuration.entity_types.replace(
                    EntityTypeConfiguration(
                        DummyNonPublicFacingEntityOne.plugin, generate_html_list=True
                    )
                )
                with pytest.raises(HumanFacingException) as exc_info:
                    async with sut:
                        pass
        assert 'data["entity_types"]["dummy-non-public-facing-one"]' in str(
            exc_info.value
        )

    async def test_extensions__should_enable_betty_extensions(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            extensions = await sut.extensions

            for betty_extension in await temporary_app.plugins(ExtensionDefinition):
                if betty_extension.id.startswith("betty-"):
                    assert betty_extension.id in extensions

    async def test_extensions__should_assert_requirement(
        self, temporary_app: App
    ) -> None:
        with ExtensionDefinition.type.override_discovery(
            _DummyExtensionWithUnmetRequirement.plugin
        ):
            async with Project.new_temporary(temporary_app) as sut:
                sut.configuration.extensions.enable(_DummyExtensionWithUnmetRequirement)
                with pytest.raises(RequirementError):
                    async with sut:
                        pass

    @pytest.mark.parametrize(
        "enable",
        [
            [_DummyExtensionA, _DummyExtensionB],
            [_DummyExtensionB, _DummyExtensionA],
        ],
    )
    async def test_extensions__should_sort_by_plugin_id(
        self, enable: Sequence[type[Extension]], temporary_app: App
    ) -> None:
        with ExtensionDefinition.type.override_discovery(
            _DummyExtensionA.plugin, _DummyExtensionB.plugin
        ):
            async with Project.new_temporary(temporary_app) as sut:
                sut.configuration.extensions.enable(*enable)
                async with sut:
                    extensions = [
                        extension.plugin
                        for extension in (await sut.extensions).flatten()
                    ]
                    assert extensions.index(_DummyExtensionA.plugin) < extensions.index(
                        _DummyExtensionB.plugin
                    )

    async def test_ancestry__with___init___ancestry(self, temporary_app: App) -> None:
        ancestry = Ancestry()
        async with (
            Project.new_temporary(temporary_app, ancestry=ancestry) as sut,
            sut,
        ):
            assert sut.ancestry is ancestry

    async def test_ancestry__without___init___ancestry(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            sut.ancestry  # noqa B018

    async def test_app(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            assert sut.app is temporary_app

    async def test_assets__without_extensions(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            assets = await sut.assets
            assert len(assets.assets_directory_paths) == 2

    async def test_assets__with_extension_without_assets_directory(
        self, temporary_app: App
    ) -> None:
        with ExtensionDefinition.type.override_discovery(DummyExtension.plugin):
            async with Project.new_temporary(temporary_app) as sut:
                sut.configuration.extensions.enable(DummyExtension)
                async with sut:
                    assets = await sut.assets
                    assert len(assets.assets_directory_paths) == 2

    async def test_assets__with_extension_with_assets_directory(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        with ExtensionDefinition.type.override_discovery(
            _DummyExtensionWithAssetsDirectory.plugin
        ):
            async with Project.new_temporary(temporary_app) as sut:
                sut.configuration.extensions.enable(_DummyExtensionWithAssetsDirectory)
                async with sut:
                    assets = await sut.assets
                    assert len(assets.assets_directory_paths) == 3

    async def test_jinja2_environment(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            await sut.jinja2_environment

    async def test_localizers(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            localizers = await sut.localizers
            assert localizers is await sut.localizers

    async def test_name__with_configuration_name(self, temporary_app: App) -> None:
        name = "hello-world"
        async with Project.new_temporary(temporary_app) as sut:
            sut.configuration.name = name
            async with sut:
                assert sut.name == name

    async def test_name__without_configuration_name(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            sut.name  # noqa B018

    async def test_renderer(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            await sut.renderer

    async def test_url_generator(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            await sut.url_generator

    async def test_new_target(self, temporary_app: App) -> None:
        class Dependent:
            pass

        async with Project.new_temporary(temporary_app) as sut, sut:
            await sut.new_target(Dependent)

    async def test_new_target__with_project_dependent_factory(
        self, temporary_app: App
    ) -> None:
        class Dependent(ProjectDependentFactory):
            def __init__(self, project: Project):
                self.project = project

            @override
            @classmethod
            async def new_for_project(cls, project: Project) -> Self:
                return cls(project)

        async with Project.new_temporary(temporary_app) as sut, sut:
            dependent = await sut.new_target(Dependent)
            assert dependent.project is sut

    async def test_new_target__with_app_dependent_factory(
        self, temporary_app: App
    ) -> None:
        class Dependent(AppDependentFactory):
            def __init__(self, app: App):
                self.app = app

            @override
            @classmethod
            async def new_for_app(cls, app: App) -> Self:
                return cls(app)

        async with Project.new_temporary(temporary_app) as sut, sut:
            dependent = await sut.new_target(Dependent)
            assert dependent.app is temporary_app

    async def test_logo__with_configuration(
        self, temporary_app: App, tmp_path: Path
    ) -> None:
        logo = tmp_path / "logo.png"
        async with Project.new_temporary(temporary_app) as sut:
            sut.configuration.logo = logo
            async with sut:
                assert sut.logo == logo

    async def test_logo__without_configuration(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            assert sut.logo.exists()

    async def test_copyright_notice(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            assert await sut.copyright_notice is await sut.copyright_notice

    async def test_license(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            assert await sut.license is await sut.license

    async def test_privatizer(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            sut.privatizer  # noqa B018

    async def test_new_resource_context(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as sut, sut:
            assert await sut.new_resource_context()


class TestProjectContext:
    async def test_project(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ProjectContext(project)
            assert sut.project is project


class TestProjectSchema(SchemaTestBase):
    @staticmethod
    def _sut_params() -> Iterable[tuple[str, bool]]:
        for url in (
            "http://example.com",
            "https://example.com",
            "https://example.com/root-path",
        ):
            for clean_urls in (True, False):
                yield url, clean_urls

    @override
    @pytest.fixture(params=_sut_params())
    async def sut(
        self, temporary_app: App, request: pytest.FixtureRequest
    ) -> SchemaTestBaseSut:
        url, clean_urls = request.param
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.url = url
            project.configuration.clean_urls = clean_urls
            async with project:
                return (
                    await ProjectSchema.new_for_project(project),
                    [
                        await betty.ancestry.person.Person().dump_linked_data(project),
                        await betty.ancestry.place.Place().dump_linked_data(project),
                        await betty.ancestry.event.Event().dump_linked_data(project),
                    ],
                    [],
                )

    @pytest.mark.parametrize(
        "clean_urls",
        [
            True,
            False,
        ],
    )
    async def test_new_for_project(self, clean_urls: bool, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = await ProjectSchema.new_for_project(project)
        JsonSchemaSchema().validate(sut.schema)

    async def test_def_url(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            def_name = "myFirstDefinition"
            assert def_name in await ProjectSchema.def_url(project, def_name)

    async def test_url(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            assert "http" in await ProjectSchema.url(project)

    async def test_www_path(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            assert str(ProjectSchema.www_path(project))


class TestProjectExtensions:
    async def test___contains____without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert DummyExtension not in sut

    async def test___contains____with_unknown_extension(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ProjectExtensions([[DummyExtension(project)]])
            assert DummyConfigurableExtension not in sut

    async def test___contains____with_known_extension(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ProjectExtensions([[DummyExtension(project)]])
            assert DummyExtension in sut

    async def test___getitem____without_extensions(self) -> None:
        sut = ProjectExtensions([])
        with pytest.raises(KeyError):
            sut[DummyExtension]

    async def test___getitem____with_unknown_extension(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ProjectExtensions([[DummyExtension(project)]])
            with pytest.raises(KeyError):
                sut[DummyConfigurableExtension]

    async def test___getitem____with_known_extension(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            sut = ProjectExtensions([[DummyExtension(project)]])
            sut[DummyExtension]

    async def test___iter____without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert list(iter(sut)) == []

    async def test___iter____with_extensions_in_a_single_batch(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            extension_one = DummyExtension(project)
            extension_two = await DummyConfigurableExtension.new_for_project(project)
            sut = ProjectExtensions([[extension_one, extension_two]])
            actual = [list(batch) for batch in iter(sut)]
            assert len(actual) == 1
            assert len(actual[0]) == 2
            assert actual[0][0] is extension_one
            assert actual[0][1] is extension_two

    async def test___iter____with_extensions_in_multiple_batches(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            extension_one = DummyExtension(project)
            extension_two = await DummyConfigurableExtension.new_for_project(project)
            sut = ProjectExtensions([[extension_one], [extension_two]])
            actual = [list(batch) for batch in iter(sut)]
            assert len(actual) == 2
            assert len(actual[0]) == 1
            assert len(actual[1]) == 1
            assert actual[0][0] is extension_one
            assert actual[1][0] is extension_two

    async def test_flatten__without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert list(sut.flatten()) == []

    async def test_flatten__with_extensions_in_a_single_batch(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            extension_one = DummyExtension(project)
            extension_two = await DummyConfigurableExtension.new_for_project(project)
            sut = ProjectExtensions([[extension_one, extension_two]])
            actual = list(sut.flatten())
            assert len(actual) == 2
            assert actual[0] is extension_one
            assert actual[1] is extension_two

    async def test_flatten__with_extensions_in_multiple_batches(
        self, temporary_app: App
    ) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            extension_one = DummyExtension(project)
            extension_two = await DummyConfigurableExtension.new_for_project(project)
            sut = ProjectExtensions([[extension_one], [extension_two]])
            actual = list(sut.flatten())
            assert len(actual) == 2
            assert actual[0] is extension_one
            assert actual[1] is extension_two
