"""
Test utilities for :py:mod:`betty.project.extension.maps`.
"""

import re  # noqa I001
from collections.abc import AsyncIterator, Iterable
from pathlib import Path
from shutil import copytree

import pytest
from aiofiles.tempfile import TemporaryDirectory
from geopy import Point
from playwright.async_api import Page, expect

from betty import serve
from betty.ancestry.name import Name
from betty.ancestry.place import Place
from betty.app import App
from betty.locale.localizable import Plain
from betty.plugin import PluginIdentifier
from betty.project import Project
from betty.project.extension import ExtensionDefinition, Extension
from betty.project.extension.maps import Maps
from betty.project.generate import generate
from betty.serve import Server
from betty.tests.conftest import check_skip_playwright

_PLACE_ID = "P0001"
_PLACE_NAME = "My First Place"


class MapsTestBase:
    """
    A base class for testing maps.
    """

    def get_other_extensions(
        self,
    ) -> Iterable[PluginIdentifier[ExtensionDefinition, Extension]]:
        """
        Get the other extensions to enable while performing the tests.

        This is meant to test maps functionality against other extensions that modify maps behavior, such as themes.
        """
        raise NotImplementedError

    @pytest.fixture(scope="session")
    async def server(self) -> AsyncIterator[Server]:
        """
        Serve a test page with a map, navigate to it, and return the Playwright Page fixture.
        """
        async with (
            TemporaryDirectory() as cache_directory_path_str,
            App.new_temporary(
                cache_directory_path=Path(cache_directory_path_str)
            ) as app,
            app,
            Project.new_temporary(app) as project,
        ):
            project.configuration.extensions.enable(Maps, *self.get_other_extensions())
            project.ancestry.add(
                Place(
                    id=_PLACE_ID,
                    coordinates=Point(52.37277778, 4.89361111),
                    names=[Name(Plain(_PLACE_NAME))],
                ),
            )
            copytree(
                Path(__file__).parent / "assets",
                project.configuration.assets_directory_path,
            )
            async with project:
                await generate(project)
                async with await serve.BuiltinProjectServer.new_for_project(
                    project
                ) as server:
                    yield server

    @pytest.mark.asyncio(loop_scope="session")
    @check_skip_playwright
    async def test_ui(self, page: Page, server: Server) -> None:
        """
        Test maps' web user interface.
        """
        await page.goto(f"{server.public_url}/map.html")
        map_element = page.locator(".map")

        full_screen_button = map_element.locator(".map-control-full-screen button")
        await full_screen_button.click()
        await expect(page.locator(".map:fullscreen")).to_be_visible()
        await full_screen_button.click()
        await expect(page.locator(".map:fullscreen")).not_to_be_visible()

        zoom_in_button = map_element.locator(".map-control-zoom-in button")
        await zoom_in_button.click()

        zoom_out_button = map_element.locator(".map-control-zoom-out button")
        await zoom_out_button.click()

        map_width, map_height = await map_element.evaluate(
            "mapElement => [mapElement.getBoundingClientRect().width, mapElement.getBoundingClientRect().height]"
        )
        await map_element.click(position={"x": map_width / 2, "y": map_height / 2})
        selected_place = map_element.locator(".map-selected-place")
        await expect(selected_place).to_have_class(
            re.compile("map-selected-place-visible")
        )
        await expect(selected_place).to_contain_text(_PLACE_NAME)
        selected_place_close_button = selected_place.locator(
            ".map-selected-place-close"
        )
        await selected_place_close_button.click()
        await expect(selected_place).not_to_have_class(
            re.compile("map-selected-place-visible")
        )
