import pytest

from betty.plugins.extension.http_api_doc import HttpApiDoc
from betty.project.generate import generate
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.tests.conftest import check_skip_webpack_entry_point_provider


class TestHttpApiDoc:
    @pytest.mark.order(0)
    @check_skip_webpack_entry_point_provider
    async def test_generate(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(service_plugins=[HttpApiDoc]) as project:
            await generate(project)
            assert (project.www_directory / "api" / "index.html").is_file()
            assert (
                project.www_directory / "js" / "webpack" / "http-api-doc.js"
            ).is_file()
