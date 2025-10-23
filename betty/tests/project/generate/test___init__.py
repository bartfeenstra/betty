from pathlib import Path

import aiofiles

from betty.ancestry.person import Person
from betty.app import App
from betty.project import Project
from betty.project.config import LocaleConfiguration
from betty.project.generate import generate
from betty.test_utils.jinja2 import assert_betty_html


async def test_generate__html_lang(new_temporary_app: App) -> None:
    async with Project.new_temporary(new_temporary_app) as project:
        project.configuration.locales["en-US"].alias = "en"
        project.configuration.locales.append(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            )
        )
        async with project:
            await generate(project)
            async with aiofiles.open(
                await assert_betty_html(project, "/nl/index.html")
            ) as f:
                html = await f.read()
                assert '<html lang="nl-NL"' in html


async def test_generate__links(new_temporary_app: App) -> None:
    async with Project.new_temporary(new_temporary_app) as project:
        project.configuration.locales.replace(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            ),
            LocaleConfiguration(
                "en-US",
                alias="en",
            ),
        )
        async with project:
            await generate(project)
            async with aiofiles.open(
                await assert_betty_html(project, "/nl/index.html")
            ) as f:
                html = await f.read()
                assert (
                    '<link rel="canonical" href="https://example.com/nl/index.html" hreflang="nl-NL" type="text/html">'
                    in html
                )
                assert (
                    '<link rel="alternate" href="/en/index.html" hreflang="en-US" type="text/html">'
                    in html
                )
            async with aiofiles.open(
                await assert_betty_html(project, "/en/index.html")
            ) as f:
                html = await f.read()
                assert (
                    '<link rel="canonical" href="https://example.com/en/index.html" hreflang="en-US" type="text/html">'
                    in html
                )
                assert (
                    '<link rel="alternate" href="/nl/index.html" hreflang="nl-NL" type="text/html">'
                    in html
                )


async def test_generate__links_for_entity_pages(new_temporary_app: App) -> None:
    async with Project.new_temporary(new_temporary_app) as project:
        project.configuration.locales.replace(
            LocaleConfiguration(
                "nl-NL",
                alias="nl",
            ),
            LocaleConfiguration(
                "en-US",
                alias="en",
            ),
        )
        person = Person(id="PERSON1")
        project.ancestry.add(person)
        async with project:
            await generate(project)
            async with aiofiles.open(
                await assert_betty_html(
                    project, f"/nl/person/{person.public_id}/index.html"
                )
            ) as f:
                html = await f.read()
            assert (
                f'<link rel="canonical" href="https://example.com/nl/person/{person.public_id}/index.html" hreflang="nl-NL" type="text/html">'
                in html
            )
            assert (
                f'<link rel="alternate" href="/en/person/{person.public_id}/index.html" hreflang="en-US" type="text/html">'
                in html
            )
            assert (
                f'<link rel="alternate" href="/person/{person.public_id}/index.json" hreflang="und" type="application/json">'
                in html
            )
            async with aiofiles.open(
                await assert_betty_html(
                    project, f"/en/person/{person.public_id}/index.html"
                )
            ) as f:
                html = await f.read()
            assert (
                f'<link rel="canonical" href="https://example.com/en/person/{person.public_id}/index.html" hreflang="en-US" type="text/html">'
                in html
            )
            assert (
                f'<link rel="alternate" href="/nl/person/{person.public_id}/index.html" hreflang="nl-NL" type="text/html">'
                in html
            )
            assert (
                f'<link rel="alternate" href="/person/{person.public_id}/index.json" hreflang="und" type="application/json">'
                in html
            )


class TestResourceOverride:
    async def test(self, new_temporary_app: App) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            localized_assets_directory_path = (
                Path(project.configuration.assets_directory_path)
                / "public"
                / "localized"
            )
            localized_assets_directory_path.mkdir(parents=True)
            async with aiofiles.open(
                str(localized_assets_directory_path / "index.html.j2"), "w"
            ) as f:
                await f.write("{% block page_content %}Betty was here{% endblock %}")
            async with project:
                await generate(project)
                async with aiofiles.open(
                    project.configuration.www_directory_path / "index.html"
                ) as f:
                    assert "Betty was here" in await f.read()
