from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Self

import pytest
from typing_extensions import override

from betty.ancestry import Ancestry
from betty.app import App
from betty.app.factory import AppDependentFactory, AppDependentSelfFactory
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import Project, ProjectContext, ProjectExtensions
from betty.project.config import LocaleConfiguration, ProjectConfiguration
from betty.project.extension import Extension, ExtensionPlugin
from betty.project.factory import ProjectDependentFactory, ProjectDependentSelfFactory
from betty.requirement import Requirement, StaticRequirement, UnmetRequirement
from betty.serde.format import FormatError
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.test_utils.plugin import DummyPluginDefinition
from betty.test_utils.project.extension import DummyExtensionOne, DummyExtensionTwo

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.service.level import ServiceLevel


class _DummyExtension(ProjectDependentSelfFactory, Extension):
    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
        return cls(project=project)


@ExtensionPlugin(
    "dummy-with-assets-directory",
    label=DUMMY_LOCALIZABLE,
    assets_directory_path=Path(__file__).parent
    / "dummy-with-assets-directory"
    / "assets",
)
class _DummyExtensionWithAssetsDirectory(_DummyExtension):
    pass


@ExtensionPlugin("dummy-unmet-requirement", label=DUMMY_LOCALIZABLE)
class _DummyExtensionWithUnmetRequirement(_DummyExtension):
    @override
    @classmethod
    async def requirement(cls, level: ServiceLevel, /) -> Requirement | None:
        return StaticRequirement(DUMMY_LOCALIZABLE)


@ExtensionPlugin("dummy-a", label=DUMMY_LOCALIZABLE)
class _DummyExtensionA(_DummyExtension):
    pass


@ExtensionPlugin("dummy-b", label=DUMMY_LOCALIZABLE)
class _DummyExtensionB(_DummyExtension):
    pass


class TestProject:
    async def test_requires_project__with_global(self) -> None:
        subject = "My First Subject"
        requires = await Project.requires(None, subject)
        assert isinstance(requires, Requirement)
        assert subject in requires.localize(DEFAULT_LOCALIZER)

    async def test_requires_project__with_app(self, isolated_app: App) -> None:
        subject = "My First Subject"
        requires = await Project.requires(isolated_app, subject)
        assert isinstance(requires, Requirement)
        assert subject in requires.localize(DEFAULT_LOCALIZER)

    async def test_requires_project__with_project(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            assert await Project.requires(project, "") is project

    async def test_plugins(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            await sut.plugins(DummyPluginDefinition)

    async def test_new__without_ancestry(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        Project(isolated_app, tmp_path / "betty.json")

    async def test_new__with_ancestry(self, isolated_app: App, tmp_path: Path) -> None:
        ancestry = Ancestry()
        sut = Project(
            isolated_app,
            tmp_path / "betty.json",
            ancestry=ancestry,
        )
        assert sut.ancestry is ancestry

    async def test_new_temporary__without_configuration(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        async with Project.new_isolated(isolated_app):
            pass

    async def test_new_temporary__with_configuration(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        configuration = ProjectConfiguration()
        async with Project.new_isolated(
            isolated_app, configuration=configuration
        ) as sut:
            assert sut.configuration is configuration

    async def test_bootstrap__should_initialize_extensions(
        self, isolated_app: App
    ) -> None:
        with ExtensionPlugin.type.override_discovery(DummyExtensionOne.plugin):
            async with Project.new_isolated(isolated_app) as sut:
                sut.configuration.extensions.enable(DummyExtensionOne)
                async with sut:
                    extensions = await sut.extensions
                    extension = extensions[DummyExtensionOne]
                    assert extension.bootstrapped

    async def test_extensions__should_enable_betty_extensions(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            extensions = await sut.extensions

            for betty_extension in await isolated_app.plugins(ExtensionPlugin):
                if betty_extension.id.startswith("betty-"):
                    assert betty_extension.id in extensions

    async def test_extensions__should_assert_requirement(
        self, isolated_app: App
    ) -> None:
        with ExtensionPlugin.type.override_discovery(
            _DummyExtensionWithUnmetRequirement.plugin
        ):
            async with Project.new_isolated(isolated_app) as sut:
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
        self, enable: Sequence[type[Extension]], isolated_app: App
    ) -> None:
        with ExtensionPlugin.type.override_discovery(
            _DummyExtensionA.plugin, _DummyExtensionB.plugin
        ):
            async with Project.new_isolated(isolated_app) as sut:
                sut.configuration.extensions.enable(*enable)
                async with sut:
                    extensions = [
                        extension.plugin
                        for extension in (await sut.extensions).flatten()
                    ]
                    assert extensions.index(_DummyExtensionA.plugin) < extensions.index(
                        _DummyExtensionB.plugin
                    )

    async def test_ancestry__with___init___ancestry(self, isolated_app: App) -> None:
        ancestry = Ancestry()
        async with (
            Project.new_isolated(isolated_app, ancestry=ancestry) as sut,
            sut,
        ):
            assert sut.ancestry is ancestry

    async def test_ancestry__without___init___ancestry(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            sut.ancestry  # noqa B018

    async def test_app(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            assert sut.app is isolated_app

    async def test_assets__without_extensions(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            assets = await sut.assets
            assert len(assets.assets_directory_paths) == 2

    async def test_assets__with_extension_without_assets_directory(
        self, isolated_app: App
    ) -> None:
        with ExtensionPlugin.type.override_discovery(DummyExtensionOne.plugin):
            async with Project.new_isolated(isolated_app) as sut:
                sut.configuration.extensions.enable(DummyExtensionOne)
                async with sut:
                    assets = await sut.assets
                    assert len(assets.assets_directory_paths) == 2

    async def test_assets__with_extension_with_assets_directory(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        with ExtensionPlugin.type.override_discovery(
            _DummyExtensionWithAssetsDirectory.plugin
        ):
            async with Project.new_isolated(isolated_app) as sut:
                sut.configuration.extensions.enable(_DummyExtensionWithAssetsDirectory)
                async with sut:
                    assets = await sut.assets
                    assert len(assets.assets_directory_paths) == 3

    async def test_jinja2_environment(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            await sut.jinja2_environment

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
            sut.name  # noqa B018

    async def test_renderer(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            await sut.renderer

    async def test_url_generator(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            await sut.url_generator

    async def test_new_target(self, isolated_app: App) -> None:
        class Dependent:
            pass

        async with Project.new_isolated(isolated_app) as sut, sut:
            await sut.new_target(Dependent)

    async def test_new_target__with_project_dependent_factory(
        self, isolated_app: App
    ) -> None:
        class _Factory(ProjectDependentFactory[Project]):
            @override
            async def new_for_project(self, project: Project, /) -> Project:
                return project

        async with Project.new_isolated(isolated_app) as sut, sut:
            target = await sut.new_target(_Factory())
            assert target is sut

    async def test_new_target__with_project_dependent_self_factory(
        self, isolated_app: App
    ) -> None:
        class Dependent(ProjectDependentSelfFactory):
            def __init__(self, project: Project):
                self.project = project

            @override
            @classmethod
            async def new_for_project(cls, project: Project, /) -> Self:
                return cls(project)

        async with Project.new_isolated(isolated_app) as sut, sut:
            dependent = await sut.new_target(Dependent)
            assert dependent.project is sut

    async def test_new_target__with_app_dependent_factory(
        self, isolated_app: App
    ) -> None:
        class _Factory(AppDependentFactory[App]):
            @override
            async def new_for_app(self, app: App, /) -> App:
                return app

        async with Project.new_isolated(isolated_app) as sut, sut:
            target = await sut.new_target(_Factory())
            assert target is isolated_app

    async def test_new_target__with_app_dependent_self_factory(
        self, isolated_app: App
    ) -> None:
        class Dependent(AppDependentSelfFactory):
            def __init__(self, app: App):
                self.app = app

            @override
            @classmethod
            async def new_for_app(cls, app: App, /) -> Self:
                return cls(app)

        async with Project.new_isolated(isolated_app) as sut, sut:
            dependent = await sut.new_target(Dependent)
            assert dependent.app is isolated_app

    async def test_logo__with_configuration(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        logo = tmp_path / "logo.png"
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
            sut.privatizer  # noqa B018

    async def test_new_resource_context(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as sut, sut:
            assert await sut.new_resource_context()

    async def test_configuration_file_path(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        configuration_file_path = tmp_path / "init.json"
        sut = Project(isolated_app, configuration_file_path)
        assert sut.configuration_file_path == configuration_file_path

    async def test_set_configuration_file_path(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = Project(isolated_app, tmp_path / "init.json")
        configuration_file_path = tmp_path / "set.json"
        await sut.set_configuration_file_path(configuration_file_path)
        # Assert that setting the path to its existing value is a no-op.
        await sut.set_configuration_file_path(configuration_file_path)

    async def test_set_configuration_file_path__with_unsupported_format(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = Project(isolated_app, tmp_path / "init")
        configuration_file_path = tmp_path / "set"
        with pytest.raises(FormatError):
            await sut.set_configuration_file_path(configuration_file_path)

    async def test_project_directory_path(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = Project(isolated_app, tmp_path / "betty.json")
        assert sut.project_directory_path == tmp_path

    async def test_output_directory_path(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = Project(isolated_app, tmp_path / "betty.json")
        assert tmp_path in sut.output_directory_path.parents

    async def test_assets_directory_path(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = Project(isolated_app, tmp_path / "betty.json")
        assert tmp_path in sut.assets_directory_path.parents

    async def test_www_directory_path(self, isolated_app: App, tmp_path: Path) -> None:
        sut = Project(isolated_app, tmp_path / "betty.json")
        assert tmp_path in sut.www_directory_path.parents

    async def test_localize_www_directory_path__monolingual(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = Project(isolated_app, tmp_path / "betty.json")
        actual = sut.localize_www_directory_path(DEFAULT_LOCALE)
        assert tmp_path in actual.parents
        assert DEFAULT_LOCALE_TAG not in str(actual)

    async def test_localize_www_directory_path__multilingual(
        self, isolated_app: App, tmp_path: Path
    ) -> None:
        sut = Project(isolated_app, tmp_path / "betty.json")
        sut.configuration.locales.append(LocaleConfiguration("nl-NL"))
        actual = sut.localize_www_directory_path(DEFAULT_LOCALE)
        assert tmp_path in actual.parents
        assert DEFAULT_LOCALE_TAG in str(actual)


class TestProjectContext:
    async def test_project(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = ProjectContext(project)
            assert sut.project is project


class TestProjectExtensions:
    async def test___contains____without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert DummyExtensionOne not in sut

    async def test___contains____with_unknown_extension(self) -> None:
        sut = ProjectExtensions([[]])
        assert DummyExtensionOne not in sut

    async def test___contains____with_known_extension(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = ProjectExtensions([[DummyExtensionOne(project=project)]])
            assert DummyExtensionOne in sut

    async def test___getitem____without_extensions(self) -> None:
        sut = ProjectExtensions([])
        with pytest.raises(KeyError):
            sut[DummyExtensionOne]

    async def test___getitem____with_unknown_extension(self) -> None:
        sut = ProjectExtensions([[]])
        with pytest.raises(KeyError):
            sut[DummyExtensionOne]

    async def test___getitem____with_known_extension(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = ProjectExtensions([[DummyExtensionOne(project=project)]])
            sut[DummyExtensionOne]

    async def test___iter____without_extensions(self) -> None:
        sut = ProjectExtensions([])
        assert list(iter(sut)) == []

    async def test___iter____with_extensions_in_a_single_batch(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            extension_one = DummyExtensionOne(project=project)
            extension_two = DummyExtensionTwo(project=project)
            sut = ProjectExtensions([[extension_one, extension_two]])
            actual = [list(batch) for batch in iter(sut)]
            assert len(actual) == 1
            assert len(actual[0]) == 2
            assert actual[0][0] is extension_one
            assert actual[0][1] is extension_two

    async def test___iter____with_extensions_in_multiple_batches(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            extension_one = DummyExtensionOne(project=project)
            extension_two = DummyExtensionTwo(project=project)
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
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            extension_one = DummyExtensionOne(project=project)
            extension_two = DummyExtensionTwo(project=project)
            sut = ProjectExtensions([[extension_one, extension_two]])
            actual = list(sut.flatten())
            assert len(actual) == 2
            assert actual[0] is extension_one
            assert actual[1] is extension_two

    async def test_flatten__with_extensions_in_multiple_batches(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            extension_one = DummyExtensionOne(project=project)
            extension_two = DummyExtensionTwo(project=project)
            sut = ProjectExtensions([[extension_one], [extension_two]])
            actual = list(sut.flatten())
            assert len(actual) == 2
            assert actual[0] is extension_one
            assert actual[1] is extension_two
