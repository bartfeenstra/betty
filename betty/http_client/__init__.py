"""
The HTTP client API.
"""

from aiohttp import ClientError
from aiohttp.client_middlewares import ClientHandlerType
from aiohttp.client_reqrep import ClientRequest, ClientResponse

from betty.locale.localizable import Plain
from betty.user import User


class ClientErrorToUserMessageMiddleware:
    """
    Log client errors to a user.
    """

    def __init__(self, user: User):
        self._user = user

    async def __call__(
        self, request: ClientRequest, handler: ClientHandlerType
    ) -> ClientResponse:
        """
        Call the middleware.
        """
        try:
            return await handler(request)
        except ClientError as error:
            await self._user.message_debug(Plain(str(error)))
            raise
