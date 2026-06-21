from pathlib import Path

import pytest
import requests
from pytest_mock import MockerFixture
from requests import Response

from betty.functools import Do
from betty.servers.documentation import DocumentationServer
from betty.test_utils.user import StaticUser


class TestDocumentationServer:
    @pytest.mark.order(0)
    async def test(self, mocker: MockerFixture, tmp_path: Path) -> None:
        mocker.patch("webbrowser.open_new_tab")
        async with DocumentationServer(tmp_path, user=StaticUser()) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)
