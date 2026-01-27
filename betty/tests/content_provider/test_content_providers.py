from gettext import NullTranslations
from pathlib import Path
from typing import cast

import aiofiles
import pytest
from aiofiles.os import makedirs
from typing_extensions import override

from betty.ancestry.note import Note
from betty.app import App
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.content_provider import ContentProvider, ContentProviderDefinition
from betty.content_provider.content_providers import (
    Box,
    BoxConfiguration,
    Notes,
    Render,
    RenderConfiguration,
    Template,
)
from betty.document import Document
from betty.job import Context as JobContext
from betty.locale import DEFAULT_LOCALE, DEFAULT_LOCALE_TAG
from betty.locale.localizable import LocalizableLike
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localize import Localizer
from betty.plugin.config import PluginConfiguration
from betty.project import Project
from betty.render import RenderDispatcher
from betty.render.plain_text import PlainText
from betty.test_utils.ancestry.has_notes import DummyHasNotes
from betty.test_utils.config import ConfigurationTestBase
from betty.test_utils.config.factory import ConfigurationDependentSelfFactoryTestBase
from betty.test_utils.content_provider import ContentProviderTestBase
from betty.test_utils.data import DataTestBase
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestRenderConfiguration(DataTestBase[RenderConfiguration]):
    sut_cls = RenderConfiguration

    def test_content(self) -> None:
        content = DUMMY_LOCALIZABLE
        sut = RenderConfiguration(content)
        assert sut.content is content


class TestRender(
    ConfigurationDependentSelfFactoryTestBase[RenderConfiguration],
    ContentProviderTestBase,
):
    @override
    @pytest.fixture
    async def sut(self) -> ContentProvider:
        return Render(
            configuration=RenderConfiguration("Hello, world!"),
            renderer=RenderDispatcher(PlainText()),
        )

    @override
    @pytest.fixture
    async def configuration_dependent_self_factory_sut(
        self,
    ) -> type[ConfigurationDependentSelfFactory[RenderConfiguration]]:
        return Render

    @override
    @pytest.fixture(params=RenderConfiguration.data().samples)
    def configuration_dependent_self_factory_sut_configuration(
        self, request: pytest.FixtureRequest
    ) -> RenderConfiguration:
        return cast(RenderConfiguration, request.param)

    @pytest.mark.parametrize(
        ("expected", "content", "locale"),
        [
            (
                "<p>One<br>\nTwo<br>\nThree</p>",
                "One\nTwo\nThree",
                DEFAULT_LOCALE,
            ),
            (
                "<p>Een<br>\nTwee<br>\nDrie</p>",
                StaticTranslations(
                    {DEFAULT_LOCALE_TAG: "One\nTwo\nThree", "nl": "Een\nTwee\nDrie"}
                ),
                "nl",
            ),
        ],
    )
    async def test_provide(
        self, expected: str, content: LocalizableLike, locale: str
    ) -> None:
        sut = Render(
            configuration=RenderConfiguration(content),
            renderer=RenderDispatcher(PlainText()),
        )
        assert (
            await sut.provide(
                document=Document(localizer=Localizer(locale, NullTranslations()))
            )
            == expected
        )


class TestTemplate:
    async def test_provide(
        self,
        isolated_app: App,
    ) -> None:
        template_name = "content/my-first-template.html.j2"
        template_path = Path(*template_name.split("/"))
        template = """
{{ document.localizer.locale }}
{{ document.resource }}
{{ document.job_context.id }}
"""
        job_context = JobContext()
        async with Project.new_isolated(isolated_app) as project, project:
            templates_directory_path = project.assets_directory_path / "templates"
            await makedirs(templates_directory_path)
            template_file_path = templates_directory_path / template_path
            await makedirs(template_file_path.parent)
            async with aiofiles.open(template_file_path, "w") as f:
                await f.write(template)

            @ContentProviderDefinition("my-first-template", label=DUMMY_LOCALIZABLE)
            class _Jinja2TemplateContentProvider(Template):
                pass

            sut = _Jinja2TemplateContentProvider(
                jinja2_environment=await project.jinja2_environment
            )
            provided_content = await sut.provide(
                document=Document(
                    "my-first-page-resource",
                    localizer=Localizer("nl-NL", NullTranslations()),
                    job_context=job_context,
                )
            )
            assert provided_content is not None
            assert (
                provided_content.strip()
                == f"nl_NL\nmy-first-page-resource\n{job_context.id}"
            )


class TestNotes(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return Notes(jinja2_environment=await project.jinja2_environment)

    async def test_provide__without_has_notes_resource(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await Notes.new_for_services(project)
            assert await sut.provide(document=Document()) is None

    async def test_provide__without_notes(self, isolated_app: App) -> None:
        has_notes = DummyHasNotes()
        async with Project.new_isolated(isolated_app) as project, project:
            project.ancestry.add(has_notes)
            sut = await Notes.new_for_services(project)
            assert await sut.provide(document=Document(has_notes)) is None

    async def test_provide__with_notes(self, isolated_app: App) -> None:
        note_text = "Hello, world!"
        has_notes = DummyHasNotes(notes=[Note(note_text)])
        async with Project.new_isolated(isolated_app) as project, project:
            project.ancestry.add(has_notes)
            sut = await Notes.new_for_services(project)
            actual = await sut.provide(document=Document(has_notes))
            assert actual is not None
            assert note_text in actual


class TestBoxConfiguration(ConfigurationTestBase[BoxConfiguration]):
    sut_cls = BoxConfiguration

    def test_content(self) -> None:
        sut = BoxConfiguration(PluginConfiguration("my-first-content"))  # ty:ignore[invalid-argument-type]
        assert sut.content[0].id == "my-first-content"

    def test_load__minimal(self) -> None:
        sut = BoxConfiguration.load(
            {
                "content": [
                    "my-first-content",
                ],
            }
        )
        assert sut.content[0].id == "my-first-content"

    def test_load__full(self) -> None:
        sut = BoxConfiguration.load(
            {
                "content": [
                    "my-first-content",
                ],
                "min_height": "MIN_HEIGHT",
                "max_height": "MAX_HEIGHT",
                "height": "HEIGHT",
                "min_width": "MIN_WIDTH",
                "max_width": "MAX_WIDTH",
                "width": "WIDTH",
            }
        )
        assert sut.min_height == "MIN_HEIGHT"
        assert sut.max_height == "MAX_HEIGHT"
        assert sut.height == "HEIGHT"
        assert sut.min_width == "MIN_WIDTH"
        assert sut.max_width == "MAX_WIDTH"
        assert sut.width == "WIDTH"

    def test_dump__minimal(self) -> None:
        sut = BoxConfiguration(PluginConfiguration("my-first-content"))  # ty:ignore[invalid-argument-type]
        assert sut.dump() == {
            "content": [
                "my-first-content",
            ],
        }

    def test_dump__full(self) -> None:
        sut = BoxConfiguration(
            PluginConfiguration("my-first-content"),  # ty:ignore[invalid-argument-type]
            min_height="MIN_HEIGHT",
            max_height="MAX_HEIGHT",
            height="HEIGHT",
            min_width="MIN_WIDTH",
            max_width="MAX_WIDTH",
            width="WIDTH",
        )
        assert sut.dump() == {
            "content": [
                "my-first-content",
            ],
            "min_height": "MIN_HEIGHT",
            "max_height": "MAX_HEIGHT",
            "height": "HEIGHT",
            "min_width": "MIN_WIDTH",
            "max_width": "MAX_WIDTH",
            "width": "WIDTH",
        }


class TestBox(ContentProviderTestBase):
    @override
    @pytest.fixture
    async def sut(self, isolated_app: App) -> ContentProvider:
        async with Project.new_isolated(isolated_app) as project, project:
            return await project.new_target(
                Box.new_for_configuration(
                    BoxConfiguration(
                        PluginConfiguration(
                            Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                        )  # ty:ignore[invalid-argument-type]
                    )
                )
            )

    async def test_provide__minimal(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await project.new_target(
                Box.new_for_configuration(
                    BoxConfiguration(
                        PluginConfiguration(
                            Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                        )  # ty:ignore[invalid-argument-type]
                    )
                )
            )
            actual = await sut.provide(document=Document())
        assert actual is not None
        assert "<div>" in actual

    async def test_provide__full(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project, project:
            sut = await project.new_target(
                Box.new_for_configuration(
                    BoxConfiguration(
                        PluginConfiguration(
                            Render, RenderConfiguration(DUMMY_LOCALIZABLE)
                        ),  # ty:ignore[invalid-argument-type]
                        min_height="MIN_HEIGHT",
                        max_height="MAX_HEIGHT",
                        height="HEIGHT",
                        min_width="MIN_WIDTH",
                        max_width="MAX_WIDTH",
                        width="WIDTH",
                    )
                )
            )
            actual = await sut.provide(document=Document())
        assert actual is not None
        assert "<div>" not in actual
        assert "min-height: MIN_HEIGHT;" in actual
        assert "max-height: MAX_HEIGHT;" in actual
        assert "height: HEIGHT;" in actual
        assert "min-width: MIN_WIDTH;" in actual
        assert "max-width: MAX_WIDTH;" in actual
        assert "width: WIDTH;" in actual
