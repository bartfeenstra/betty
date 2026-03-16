from pathlib import Path

from betty.app import App
from betty.document import Document
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugins.content.raspberry_mint_media_gallery import MediaGallery
from betty.plugins.entity.file import File
from betty.plugins.entity.file_reference import FileReference
from betty.plugins.entity.person import Person
from betty.plugins.extension.raspberry_mint import RaspberryMint
from betty.project import Project


class TestMediaGallery:
    async def test_build_template__without_has_file_references(
        self, isolated_app: App
    ) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await MediaGallery.new(project)
                assert await sut.build(document=Document(object())) is None

    async def test_build_template__with_has_file_references_without_file_references(
        self, isolated_app: App
    ) -> None:
        resource = Person()
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await MediaGallery.new(project)
                assert await sut.build(document=Document(resource)) is None

    async def test_build_template__with_has_file_references_with_file_references(
        self, isolated_app: App
    ) -> None:
        resource = Person()
        file = File(Path(__file__))
        FileReference(resource, file)
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(RaspberryMint)
            async with project:
                sut = await MediaGallery.new(project)
                actual = await sut.build(document=Document(resource))
        assert actual is not None
        assert file.label.localize(DEFAULT_LOCALIZER) in actual
