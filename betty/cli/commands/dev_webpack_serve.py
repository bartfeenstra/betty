from __future__ import annotations  # noqa D100

from typing import TYPE_CHECKING, final, Self, cast

import asyncclick as click
from typing_extensions import override

from betty.app.factory import AppDependentFactory
from betty.cli.commands import command, Command
from betty.importlib import import_any
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project.extension.webpack.build import WatchBuilder, WatchBuildWorkspace

if TYPE_CHECKING:
    from betty.app import App


@final
class DevWebpackServe(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to run a live Webpack build and serve the result.
    """

    _plugin_id = "dev-webpack-serve"
    _plugin_label = _("Run a live Webpack build and serve the result")

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def click_command(self) -> click.Command:
        localizer = await self._app.localizer
        description = self.plugin_description()

        def _workspace_callback(
            _: click.Context, __: click.Parameter, name: str
        ) -> type[WatchBuildWorkspace]:
            try:
                workspace = import_any(name)
            except ImportError as error:
                raise click.BadParameter(str(error)) from error
            if not issubclass(workspace, WatchBuildWorkspace):
                raise click.BadParameter(
                    f"{workspace} must extend {WatchBuildWorkspace}, but does not."
                )
            return cast(type[WatchBuildWorkspace], workspace)

        @command(
            self.plugin_id(),
            short_help=self.plugin_label().localize(localizer),
            help=description.localize(localizer)
            if description
            else self.plugin_label().localize(localizer),
        )
        @click.option("--pre-build-only", default=False, is_flag=True)
        @click.argument("workspace", required=True, callback=_workspace_callback)
        async def dev_webpack_serve(
            *, workspace: WatchBuildWorkspace, pre_build_only: bool
        ) -> None:
            async with WatchBuilder.new(
                await workspace.new_for_app(self._app), self._app
            ) as builder:
                # @todo This won't work simply because we create new builders and new projects.
                if pre_build_only:
                    await builder.pre_build()
                else:
                    await builder.build()

        return dev_webpack_serve
