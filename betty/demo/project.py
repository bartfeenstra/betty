"""
Create demonstration projects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.content_builder import ContentBuilderManufacturer
from betty.content_builders.raspberry_mint_columns import Columns, ColumnsData
from betty.content_builders.raspberry_mint_entity_card import EntityCard
from betty.content_builders.raspberry_mint_incomplete_translation_warning import (
    IncompleteTranslationWarning,
)
from betty.content_builders.raspberry_mint_section import Section, SectionData
from betty.content_builders.render import Render, RenderData
from betty.content_builders.wikipedia_summary import WikipediaSummary
from betty.datas.entity_reference import EntityReference
from betty.enrichers.deriver import Deriver
from betty.enrichers.wiki import Wiki
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.source import Source
from betty.extension import ExtensionManufacturer
from betty.extensions.http_api_doc import HttpApiDoc
from betty.extensions.maps import Maps
from betty.extensions.raspberry_mint import (
    Breakpoint,
    RaspberryMint,
    RaspberryMintData,
    Region,
)
from betty.extensions.spdx import Spdx
from betty.extensions.trees import Trees
from betty.license import LicenseManufacturer
from betty.links.betty_documentation import BETTY_DOCUMENTATION
from betty.links.betty_github import BETTY_GITHUB
from betty.loaders.demo import Demo
from betty.locale import default_locale
from betty.localizables.gettext import _
from betty.localizables.markup import Chain
from betty.media_types.html import HTML
from betty.project import Project

if TYPE_CHECKING:
    from betty.app import App
    from betty.pathlib import StrPath


async def create_project(
    app: App, directory: StrPath, *, url: str | None = None
) -> Project:
    """
    Create a new demonstration project.
    """
    translations = await app.translations

    return Project(
        app=app,
        author=_("Bart Feenstra and contributors"),
        directory=directory,
        enrichers=[
            Deriver,
            Wiki,
        ],
        extensions=[
            HttpApiDoc,
            Maps,
            RaspberryMint,
            Spdx,
            ExtensionManufacturer(
                RaspberryMint,
                RaspberryMintData(
                    regional_content={
                        Region.FRONT_PAGE_CONTENT: [
                            ContentBuilderManufacturer(
                                Columns,
                                ColumnsData([[IncompleteTranslationWarning]]),
                            ),
                            ContentBuilderManufacturer(
                                Section,
                                SectionData(
                                    ContentBuilderManufacturer(
                                        Columns,
                                        ColumnsData(
                                            [
                                                [
                                                    ContentBuilderManufacturer(
                                                        Render,
                                                        RenderData(
                                                            Chain(
                                                                "<h2>",
                                                                _("Get started"),
                                                                "</h2>"
                                                                '<a href="https://betty.readthedocs.io/" class="view-more">',
                                                                _(
                                                                    "Read the documentation"
                                                                ),
                                                                "</a>",
                                                                '<a href="https://github.com/bartfeenstra/betty/" class="view-more">',
                                                                _("View the code"),
                                                                "</a>",
                                                            ),
                                                            HTML,
                                                        ),
                                                    ),
                                                ],
                                                [
                                                    ContentBuilderManufacturer(
                                                        Render,
                                                        RenderData(
                                                            Chain(
                                                                "<p>",
                                                                _(
                                                                    "Betty was named after <a href=\"betty-entity://person/betty-demo-liberta-lankester\">Liberta 'Betty' Lankester</a>, and this website shows a small sample of her family history. You can browse the pages about her and some of her family to get an idea of what a Betty site looks like."
                                                                ),
                                                                "</p>",
                                                            ),
                                                            HTML,
                                                        ),
                                                    ),
                                                ],
                                            ],
                                            width={
                                                Breakpoint.XS: [12, 12],
                                                Breakpoint.MD: [5, 6],
                                                Breakpoint.LG: [4, 7],
                                            },
                                        ),
                                    ),
                                    heading=_("Welcome"),
                                    visually_hide_heading=True,
                                ),
                            ),
                            ContentBuilderManufacturer(
                                Section,
                                SectionData(
                                    ContentBuilderManufacturer(
                                        Columns,
                                        ColumnsData(
                                            [
                                                [
                                                    ContentBuilderManufacturer(
                                                        EntityCard,
                                                        EntityReference(
                                                            Place,
                                                            "betty-demo-amsterdam",
                                                        ),
                                                    )
                                                ],
                                                [
                                                    ContentBuilderManufacturer(
                                                        EntityCard,
                                                        EntityReference(
                                                            Person,
                                                            "betty-demo-liberta-lankester",
                                                        ),
                                                    )
                                                ],
                                                [
                                                    ContentBuilderManufacturer(
                                                        EntityCard,
                                                        EntityReference(
                                                            Place,
                                                            "betty-demo-netherlands",
                                                        ),
                                                    )
                                                ],
                                            ],
                                            width={
                                                Breakpoint.XS: [12, 12, 12],
                                                Breakpoint.MD: [6, 6, 6],
                                                Breakpoint.LG: [4, 4, 4],
                                            },
                                        ),
                                    ),
                                    heading=_("Explore a family history..."),
                                ),
                            ),
                        ],
                        Region.FRONT_PAGE_SUMMARY: [
                            ContentBuilderManufacturer(
                                Render,
                                RenderData(
                                    _(
                                        "Betty is an application that takes a family tree and builds a website out of it, much like the one you are viewing right now. The more information your genealogical research contains, the more interactivity Betty can add to your site, such as media galleries, maps, and browsable family trees."
                                    )
                                ),
                            ),
                        ],
                    }
                ),
            ),
            Trees,
        ],
        generate_entity_list_html=[
            Person,
            Event,
            Place,
            Source,
        ],
        license=LicenseManufacturer("spdx-gpl-3-0-or-later"),
        links=[
            BETTY_DOCUMENTATION,
            BETTY_GITHUB,
        ],
        loaders=[
            Demo,
        ],
        locales=[
            # The first configured locale is the project default.
            default_locale,
            *[locale for locale in translations.locales if locale != default_locale],
        ],
        name="demo",
        supported_plugins=[
            WikipediaSummary,
        ],
        title=_("A Betty demonstration"),
        url=url or "https://example.com",
    )
