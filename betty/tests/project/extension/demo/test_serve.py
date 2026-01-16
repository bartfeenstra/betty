from __future__ import annotations

from typing import TYPE_CHECKING

import requests
from requests import Response

from betty.functools import Do
from betty.project.extension.demo.serve import DemoServer
from betty.test_utils.project.extension.demo.project import (
    demo_project_fetcher,  # noqa: F401
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.fetch import Fetcher
    from betty.test_utils.conftest import NewTemporaryAppFactory


class TestDemoServer:
    async def test(
        self,
        demo_project_fetcher: Fetcher,  # noqa: F811
        mocker: MockerFixture,
        new_temporary_app_factory: NewTemporaryAppFactory,
    ) -> None:
        mocker.patch("webbrowser.open_new_tab")
        async with (
            await new_temporary_app_factory(fetcher=demo_project_fetcher) as app,
            app,
            DemoServer(app=app) as server,
        ):

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)
