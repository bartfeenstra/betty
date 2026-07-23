"""
The web server API.
"""

from __future__ import annotations

import webbrowser
from abc import ABC, abstractmethod
from asyncio import to_thread
from http.client import HTTPConnection
from typing import TYPE_CHECKING, Any, Self, final
from urllib.parse import urlsplit

from betty.definition.human_facing import HumanFacingDefinition
from betty.exception import HumanFacingException
from betty.functools import Do
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import Order, OrderedPluginClsDefinition
from betty.user import Severity

if TYPE_CHECKING:
    from types import TracebackType

    from betty.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires
    from betty.user import User


class ServerNotStarted(RuntimeError):
    """
    Raised when a web server has not (fully) started yet.
    """


class Server(ABC):
    """
    A web server.
    """

    def __init__(self, *, user: User):
        self._user = user

    @abstractmethod
    async def start(self) -> None:
        """
        Start the server.
        """

    async def show(self) -> None:
        """
        Show the served site to the user.
        """
        await self._user.message(
            _("Serving your site at {url}…").format(
                url=self.public_url,
            ),
            Severity.INFO,
        )
        webbrowser.open_new_tab(self.public_url)

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the server.
        """

    @property
    @abstractmethod
    def public_url(self) -> str:
        """
        The server's public URL.
        """

    @final
    async def __aenter__(self) -> Self:
        await self.start()
        try:
            await self.assert_available()
        except BaseException:
            await self.stop()
            raise
        return self

    @final
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()

    @final
    async def assert_available(self) -> None:
        """
        Assert that this server is available.
        """
        try:
            await Do[Any, None](self.__do_assert_available).until()
        except Exception as error:
            raise HumanFacingException(
                _("The server at {url} was unreachable after starting.").format(
                    url=self.public_url
                )
            ) from error

    async def __do_assert_available(self) -> None:
        await to_thread(self.__assert_available)

    def __assert_available(self) -> None:
        url_parts = urlsplit(self.public_url)
        connection = HTTPConnection(url_parts.netloc)
        connection.request("GET", url_parts.path)
        response = connection.getresponse()
        assert 400 > response.status >= 200


@final
@PluginTypeDefinition(
    "server",
    label=_("Server"),
    label_plural=_("Servers"),
    label_countable=ngettext("{count} server", "{count} servers"),
)
class ServerDefinition(HumanFacingDefinition, OrderedPluginClsDefinition[Server]):
    """
    .. plugin_type:: server.

    A project server plugin definition.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        after: Order[ServerDefinition] = (),
        auto: bool = False,
        before: Order[ServerDefinition] = (),
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            after=after,
            auto=auto,
            before=before,
            label=label,
            description=description,
            requires=requires,
        )
