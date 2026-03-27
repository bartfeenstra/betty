from pathlib import Path

import aiofiles

from betty.plugins.entity.person import Person
from betty.project import Project, ProjectLocale
from betty.project.generate import generate
from betty.test_utils.conftest import IsolatedProjectFactory
from betty.test_utils.jinja import assert_betty_html


async def test_generate__html_lang(
    isolated_project_factory: IsolatedProjectFactory,
) -> None:
    async with isolated_project_factory(
        locales=(
            ProjectLocale(
                "en-US",
                alias="en",
            ),
            ProjectLocale(
                "nl-NL",
                alias="nl",
            ),
        ),
    ) as project:
        await generate(project)
        async with aiofiles.open(
            await assert_betty_html(project, "/nl/index.html")
        ) as f:
            html = await f.read()
            assert '<html lang="nl-NL"' in html


async def test_generate__links(
    isolated_project_factory: IsolatedProjectFactory,
) -> None:
    async with isolated_project_factory(
        locales=(
            ProjectLocale(
                "nl-NL",
                alias="nl",
            ),
            ProjectLocale(
                "en-US",
                alias="en",
            ),
        ),
    ) as project:
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


async def test_generate__links_for_entity_pages(
    isolated_project_factory: IsolatedProjectFactory,
) -> None:
    async with isolated_project_factory(
        locales=(
            ProjectLocale(
                "nl-NL",
                alias="nl",
            ),
            ProjectLocale(
                "en-US",
                alias="en",
            ),
        ),
    ) as project:
        person = Person(id="PERSON1")
        project.ancestry.add(person)
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
    async def test(self, isolated_project: Project) -> None:
        localized_assets_directory_path = (
            Path(isolated_project.assets_directory) / "public" / "localized"
        )
        localized_assets_directory_path.mkdir(parents=True)
        async with aiofiles.open(
            str(localized_assets_directory_path / "index.html.j2"), "w"
        ) as f:
            await f.write("{% block page_content %}Betty was here{% endblock %}")
        await generate(isolated_project)
        async with aiofiles.open(isolated_project.www_directory / "index.html") as f:
            assert "Betty was here" in await f.read()
