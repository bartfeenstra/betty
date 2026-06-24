from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import requests
from requests import Response

from betty.functools import Do
from betty.servers.demo import DemoServer

if TYPE_CHECKING:
    from pytest_mock import MockerFixture

    from betty.test_utils.conftest import IsolatedAppFactory


@pytest.mark.usefixtures("demo_project_aioresponses")
class TestDemoServer:
    async def test(
        self, mocker: MockerFixture, isolated_app_factory: IsolatedAppFactory
    ) -> None:
        m_generate_with_cleanup = mocker.patch(
            "betty.demo.generate.generate_with_cleanup"
        )
        mocker.patch("webbrowser.open_new_tab")
        async with isolated_app_factory() as app, DemoServer(app) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200

            await Do(requests.get, server.public_url).until(_assert_response)
        m_generate_with_cleanup.assert_awaited_once()
