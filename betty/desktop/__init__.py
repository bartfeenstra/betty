"""
The Betty desktop application.
"""

from __future__ import annotations

import asyncio
from asyncio import Task
from typing import TYPE_CHECKING, Any, Self, final

from textual.app import App as TextualApp
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Markdown, RichLog, TabbedContent
from typing_extensions import override

from betty.project.extension import EXTENSION_REPOSITORY, ConfigurableExtension
from betty.project.extension.demo.serve import DemoServer
from betty.typing import internal

if TYPE_CHECKING:
    from betty.app import App
    from betty.config import Configuration
    from betty.locale.localizer import Localizer
    from betty.project import Project


# @todo How to set DesktopUser on App as soon as we launch the desktop application?
# @todo
# @todo
# @todo
@final
@internal
class BettyApp(TextualApp[None]):
    """
    The Betty desktop Textual application.
    """

    TITLE = "Betty"

    @internal
    def __init__(self, app: App):
        super().__init__()
        self._app = app
        self._log_viewer = RichLog()

    @classmethod
    async def new(cls, app: App) -> Self:
        """
        Create a new instance.
        """
        return cls(app)

    @override
    def compose(self) -> ComposeResult:
        # @todo Where does the name show?
        yield Header(name="Betty")
        yield WelcomeWidget(self._app)
        yield self._log_viewer
        yield Footer()


@final
@internal
class WelcomeWidget(Widget):
    """
    Welcome the user, and provide entry points.
    """

    def __init__(self, app: App):
        super().__init__()
        self._app = app

    @override
    def compose(self) -> ComposeResult:
        localizer = self._app.user.localizer
        yield Markdown(localizer._("Welcome to Betty"))
        yield Button(localizer._("New project"))
        yield Button(localizer._("Open project"))
        yield Button(localizer._("View a demonstration"), action="demo")

    async def action_demo(self) -> None:
        """
        A Textual action to run the demo site.
        """
        screen = DemoScreen(self._app)
        await screen.start()
        await self.app.push_screen(screen)


@final
@internal
class DemoScreen(ModalScreen[Any]):
    """
    A modal for running the demonstration site.
    """

    # @todo Alter this
    CSS = """
    DemoScreen {      
        align: center middle;              
    }
    """

    BINDINGS = [("escape", "dismiss")]

    def __init__(self, app: App):
        super().__init__()
        self._app = app
        self._task: Task[None]

    async def start(self) -> None:
        """
        Start the demo site.
        """
        self._task = asyncio.create_task(self._serve())

    async def stop(self) -> None:
        """
        Stop the demo site.
        """
        self._task.cancel()

    async def _serve(self) -> None:
        async with DemoServer(app=self._app) as server:
            await server.show()
            while True:
                await asyncio.sleep(999)

    async def on_dismiss(self) -> None:  # noqa D102
        await self.stop()

    @override
    def compose(self) -> ComposeResult:
        # @todo Localize this
        yield Markdown("boo")
        yield Button("Close", action="dismiss")


@final
@internal
class ProjectConfigurationWidget(Widget):
    """
    Configure a project.
    """

    @internal
    def __init__(
        self,
        extensions: set[type[ConfigurableExtension[Configuration]]],
        *,
        localizer: Localizer,
    ):
        super().__init__()
        self._extensions = extensions
        self._localizer = localizer

    @classmethod
    async def new(cls, project: Project) -> Self:
        """
        Create a new instance.
        """
        return cls(
            {
                extension
                async for extension in EXTENSION_REPOSITORY
                if issubclass(extension, ConfigurableExtension)
            },
            localizer=project.app.user.localizer,
        )

    @override
    def compose(self) -> ComposeResult:
        with TabbedContent(
            *[
                extension.plugin_label().localize(self._localizer)
                for extension in self._extensions
            ]
        ):
            yield Markdown(self._localizer._("General"))
            for extension in self._extensions:
                yield Markdown(extension.plugin_id())
