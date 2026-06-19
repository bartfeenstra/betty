from betty.document_providers.webpack import Webpack
from betty.project import Project


class TestWebpack:
    async def test_new_document_vars(self, isolated_project: Project) -> None:
        sut = Webpack()
        assert sut.new_document_vars()
