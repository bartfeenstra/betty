from __future__ import annotations

from typing import TYPE_CHECKING

import requests
from requests import Response

from betty.functools import Do
from betty.project.extension.demo.serve import DemoServer
from betty.test_utils.project.extension.demo.project import (
    demo_project_aioresponses,  # noqa F401
)
from betty.tests.conftest import check_skip_webpack_entry_point_provider

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.test_utils.conftest import IsolatedAppFactory


class TestDemoServer:
    @check_skip_webpack_entry_point_provider
    async def test(
        self,
        demo_project_aioresponses: None,  # noqa F811
        mocker: MockerFixture,
        isolated_app_factory: IsolatedAppFactory,
    ) -> None:
        mocker.patch("webbrowser.open_new_tab")
        async with isolated_app_factory() as app, app, DemoServer(app=app) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)
