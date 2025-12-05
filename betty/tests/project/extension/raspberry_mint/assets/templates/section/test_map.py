from geopy import Point

from betty.ancestry.place import Place
from betty.app import App
from betty.project import Project
from betty.project.extension.maps import Maps
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal(isolated_app: App) -> None:
    async with Project.new_isolated(isolated_app) as project:
        project.configuration.extensions.enable(Maps)
        async with (
            project,
            assert_template_file(
                data={
                    "resource": await project.new_resource_context(),
                    "places": [],
                },
                extensions={RaspberryMint, Maps},
                template="section/map.html.j2",
            ) as (actual, _),
        ):
            assert actual == ""


async def test_with_places(isolated_app: App) -> None:
    place = Place(coordinates=Point(1, 1))
    async with Project.new_isolated(isolated_app) as project:
        project.configuration.extensions.enable(Maps)
        async with (
            project,
            assert_template_file(
                data={
                    "resource": await project.new_resource_context(),
                    "places": [place],
                },
                extensions={RaspberryMint, Maps},
                template="section/map.html.j2",
            ) as (actual, _),
        ):
            assert actual
