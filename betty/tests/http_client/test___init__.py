from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientError, ClientRequest, ClientResponse
from yarl import URL

from betty.http_client import ClientErrorToUserMessageMiddleware
from betty.test_utils.user import StaticUser


class TestClientErrorToUserMessageMiddleware:
    async def test___call____without_error(self) -> None:
        m_response = AsyncMock(spec=ClientResponse)
        handler_called_request = []

        async def _handler(request: ClientRequest) -> ClientResponse:
            handler_called_request.append(request)
            return m_response

        request = ClientRequest("GET", URL("https://example.com"))
        user = StaticUser()
        sut = ClientErrorToUserMessageMiddleware(user)
        assert await sut(request, _handler) is m_response
        assert handler_called_request[0] is request

    async def test___call____with_error(self) -> None:
        handler_called_request = []
        error_message = "oops!"
        error = ClientError(error_message)

        async def _handler(request: ClientRequest) -> ClientResponse:
            handler_called_request.append(request)
            raise error

        request = ClientRequest("GET", URL("https://example.com"))
        user = StaticUser()
        sut = ClientErrorToUserMessageMiddleware(user)
        with pytest.raises(ClientError) as exc_info:
            await sut(request, _handler)
        assert exc_info.value is error
        assert handler_called_request[0] is request
        user.assert_message_debug(error_message)
