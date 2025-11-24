from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Self

import pytest
from typing_extensions import override

from betty.ancestry import Ancestry
from betty.app import App
from betty.app.factory import AppDependentFactory, AppDependentSelfFactory
from betty.exception import HumanFacingException
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.model import EntityDefinition
from betty.project import Project, ProjectContext, ProjectExtensions
from betty.project.config import EntityTypeConfiguration, ProjectConfiguration
from betty.project.extension import Extension, ExtensionDefinition
from betty.project.factory import ProjectDependentFactory, ProjectDependentSelfFactory
from betty.requirement import Requirement, StaticRequirement, UnmetRequirement
from betty.test_utils.model import DummyNonPublicFacingEntityOne
from betty.test_utils.plugin import DummyPluginDefinition
from betty.test_utils.project.extension import DummyExtensionOne, DummyExtensionTwo

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.service.level import ServiceLevel


@ExtensionDefinition(
    id="dummy-with-assets-directory",
    label="",
    assets_directory_path=Path(__file__).parent
    / "dummy-with-assets-directory"
    / "assets",
)
class _DummyExtensionWithAssetsDirectory(Extension):
    pass


@ExtensionDefinition(
    id="dummy-unmet-requirement",
    label="",
)
class _DummyExtensionWithUnmetRequirement(Extension):
    @override
    @classmethod
    async def requirement(cls, level: ServiceLevel, /) -> Requirement | None:
        return StaticRequirement("")


@ExtensionDefinition(
    id="dummy-a",
    label="",
)
class _DummyExtensionA(Extension):
    pass


@ExtensionDefinition(
    id="dummy-b",
    label="",
)
class _DummyExtensionB(Extension):
    pass


class TestProject:
    async def test_requires_project__with_global(self) -> None:
        subject = "My First Subject"
        requires = await Project.requires(None, subject)
        assert isinstance(requires, Requirement)
        assert subject in requires.localize(DEFAULT_LOCALIZER)

    async def test_requires_project__with_app(self, temporary_app: App) -> None:
        subject = "My First Subject"
        requires = await Project.requires(temporary_app, subject)
        assert isinstance(requires, Requirement)
        assert subject in requires.localize(DEFAULT_LOCALIZER)

    async def test_requires_project__with_project(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project, project:
            assert await Project.requires(project, "") is project

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
        with ExtensionDefinition.type.override_discovery(DummyExtensionOne.plugin):
            async with Project.new_temporary(temporary_app) as sut:
                sut.configuration.extensions.enable(DummyExtensionOne)
                async with sut:
                    extensions = await sut.extensions
                    extension = extensions[DummyExtensionOne]
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
                with pytest.raises(UnmetRequirement):
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
        with ExtensionDefinition.type.override_discovery(DummyExtensionOne.plugin):
            async with Project.new_temporary(temporary_app) as sut:
                sut.configuration.extensions.enable(DummyExtensionOne)
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
        class _Factory(ProjectDependentFactory[Project]):
            @override
            async def new_for_project(self, project: Project, /) -> Project:
                return project

        async with Project.new_temporary(temporary_app) as sut, sut:
            target = await sut.new_target(_Factory())
            assert target is sut

    async def test_new_target__with_project_dependent_self_factory(
        self, temporary_app: App
    ) -> None:
        class Dependent(ProjectDependentSelfFactory):
            def __init__(self, project: Project):
                self.project = project

            @override
            @classmethod
            async def new_for_project(cls, project: Project, /) -> Self:
                return cls(project)

        async with Project.new_temporary(temporary_app) as sut, sut:
            dependent = await sut.new_target(Dependent)
            assert dependent.project is sut

    async def test_new_target__with_app_dependent_factory(
        self, temporary_app: App
    ) -> None:
        class _Factory(AppDependentFactory[App]):
            @override
            async def new_for_app(self, app: App, /) -> App:
                return app

        async with Project.new_temporary(temporary_app) as sut, sut:
            target = await sut.new_target(_Factory())
            assert target is temporary_app

    async def test_new_target__with_app_dependent_self_factory(
        self, temporary_app: App
    ) -> None:
        class Dependent(AppDependentSelfFactory):
            def __init__(self, app: App):
                self.app = app

            @override
            @classmethod
            async def new_for_app(cls, app: App, /) -> Self:
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


class TestProjectExtensions:
    async def test___contains____without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert DummyExtensionOne not in sut

    async def test___contains____with_unknown_extension(self) -> None:
        sut = ProjectExtensions([[]])
        assert DummyExtensionOne not in sut

    async def test___contains____with_known_extension(self) -> None:
        sut = ProjectExtensions([[DummyExtensionOne()]])
        assert DummyExtensionOne in sut

    async def test___getitem____without_extensions(self) -> None:
        sut = ProjectExtensions([])
        with pytest.raises(KeyError):
            sut[DummyExtensionOne]

    async def test___getitem____with_unknown_extension(self) -> None:
        sut = ProjectExtensions([[]])
        with pytest.raises(KeyError):
            sut[DummyExtensionOne]

    async def test___getitem____with_known_extension(self) -> None:
        sut = ProjectExtensions([[DummyExtensionOne()]])
        sut[DummyExtensionOne]

    async def test___iter____without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert list(iter(sut)) == []

    async def test___iter____with_extensions_in_a_single_batch(self) -> None:
        extension_one = DummyExtensionOne()
        extension_two = DummyExtensionTwo()
        sut = ProjectExtensions([[extension_one, extension_two]])
        actual = [list(batch) for batch in iter(sut)]
        assert len(actual) == 1
        assert len(actual[0]) == 2
        assert actual[0][0] is extension_one
        assert actual[0][1] is extension_two

    async def test___iter____with_extensions_in_multiple_batches(self) -> None:
        extension_one = DummyExtensionOne()
        extension_two = DummyExtensionTwo()
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

    async def test_flatten__with_extensions_in_a_single_batch(self) -> None:
        extension_one = DummyExtensionOne()
        extension_two = DummyExtensionTwo()
        sut = ProjectExtensions([[extension_one, extension_two]])
        actual = list(sut.flatten())
        assert len(actual) == 2
        assert actual[0] is extension_one
        assert actual[1] is extension_two

    async def test_flatten__with_extensions_in_multiple_batches(self) -> None:
        extension_one = DummyExtensionOne()
        extension_two = DummyExtensionTwo()
        sut = ProjectExtensions([[extension_one], [extension_two]])
        actual = list(sut.flatten())
        assert len(actual) == 2
        assert actual[0] is extension_one
        assert actual[1] is extension_two
