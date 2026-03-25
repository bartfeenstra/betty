import pytest

from betty.app import App
from betty.plugins.extension.http_api_doc import HttpApiDoc
from betty.project import Project
from betty.project.generate import generate
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestHttpApiDoc:
    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate(self, isolated_app: App) -> None:
        async with Project.new_isolated(isolated_app) as project:
            project.configuration.extensions.add(HttpApiDoc)
            async with project:
                await generate(project)
                assert (project.www_directory / "api" / "index.html").is_file()
                assert (
                    project.www_directory / "js" / "webpack" / "http-api-doc.js"
                ).is_file()
