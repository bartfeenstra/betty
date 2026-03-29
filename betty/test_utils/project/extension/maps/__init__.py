"""
Test utilities for :py:mod:`betty.plugins.extension.maps`.
"""

import re  # noqa: I001
from collections.abc import AsyncIterator, Iterable
from pathlib import Path
from shutil import copytree

import pytest
from geopy import Point
from playwright.async_api import Page, expect

from betty import serve
from betty.plugins.entity.place_name import PlaceName
from betty.extension import ExtensionDefinition, ExtensionManufacturer
from betty.plugin import ResolvablePluginId
from betty.plugins.entity.place import Place
from betty.plugins.extension.maps import Maps
from betty.project import Project
from betty.project.generate import generate
from betty.serve import Server
from betty.tests.conftest import (
    check_skip_playwright,
    check_skip_webpack_entry_point_provider,
)

_PLACE_ID = "P0001"
_PLACE_NAME = "My First Place"


class MapsTestBase:
    """
    A base class for testing maps.
    """

    def get_other_extensions(
        self,
    ) -> Iterable[ResolvablePluginId[ExtensionDefinition]]:
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
        async with Project.new_isolated(
            service_plugins=[
                Maps,
                *ExtensionManufacturer.resolve_sequence(self.get_other_extensions()),
            ],
        ) as project:
            project.ancestry.add(
                Place(
                    id=_PLACE_ID,
                    coordinates=Point(52.37277778, 4.89361111),
                    names=[PlaceName(_PLACE_NAME)],
                ),
            )
            copytree(
                Path(__file__).parent / "assets",
                project.assets_directory,
            )
            await generate(project)
            async with await serve.BuiltinProjectServer.new(project) as server:
                yield server

    @pytest.mark.asyncio(loop_scope="session")
    @pytest.mark.order(0)
    @check_skip_playwright
    @check_skip_webpack_entry_point_provider
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
