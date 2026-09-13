"""
Create demonstration projects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from babel import Locale

from betty import about, dirs
from betty.content_builder import NewContentBuilder
from betty.content_builders.raspberry_mint_columns import Columns, ColumnsConfig
from betty.content_builders.raspberry_mint_entity_card import EntityCard
from betty.content_builders.raspberry_mint_incomplete_translation_warning import (
    IncompleteTranslationWarning,
)
from betty.content_builders.raspberry_mint_section import Section, SectionConfig
from betty.content_builders.render import Render, RenderConfig
from betty.content_builders.wikipedia_summary import WikipediaSummary
from betty.datas.entity_reference import EntityReference
from betty.enrichers.deriver import Deriver
from betty.enrichers.wiki import Wiki
from betty.entities.event import Event
from betty.entities.person import Person
from betty.entities.place import Place
from betty.entities.source import Source
from betty.license import NewLicense
from betty.links.betty_documentation import BETTY_DOCUMENTATION
from betty.links.betty_github import BETTY_GITHUB
from betty.loaders.demo import Demo
from betty.locale import default_locale
from betty.localizables.gettext import _
from betty.localizables.markup import Chain
from betty.media_types.html import HTML
from betty.project import Project
from betty.service_provider import NewServiceProvider
from betty.service_providers.http_api_doc import HttpApiDoc
from betty.service_providers.maps import Maps
from betty.service_providers.raspberry_mint import (
    Breakpoint,
    RaspberryMint,
    RaspberryMintConfig,
    Region,
)
from betty.service_providers.spdx import Spdx
from betty.service_providers.trees import Trees

if TYPE_CHECKING:
    from betty.app import App
    from betty.pathlib import StrPath


async def create_project(
    app: App, directory: StrPath, *, url: str | None = None
) -> Project:
    """
    Create a new demonstration project.
    """
    return Project(
        app=app,
        author=_("Bart Feenstra and contributors"),
        directory=directory,
        enrichers=[
            Deriver,
            Wiki,
        ],
        service_providers=[
            HttpApiDoc,
            Maps,
            RaspberryMint,
            Spdx,
            NewServiceProvider(
                RaspberryMint,
                RaspberryMintConfig(
                    regional_content={
                        Region.FRONT_PAGE_CONTENT: [
                            NewContentBuilder(
                                Columns,
                                ColumnsConfig([IncompleteTranslationWarning]),
                            ),
                            NewContentBuilder(
                                Section,
                                SectionConfig(
                                    NewContentBuilder(
                                        Columns,
                                        ColumnsConfig(
                                            [
                                                NewContentBuilder(
                                                    Render,
                                                    RenderConfig(
                                                        Chain(
                                                            "<h2>",
                                                            _("Get started"),
                                                            "</h2>"
                                                            f'<a href="{about.url_documentation}" class="view-more">',
                                                            _("Read the documentation"),
                                                            "</a>",
                                                            f'<a href="{about.url_code}" class="view-more">',
                                                            _("View the code"),
                                                            "</a>",
                                                        ),
                                                        HTML,
                                                    ),
                                                ),
                                            ],
                                            [
                                                NewContentBuilder(
                                                    Render,
                                                    RenderConfig(
                                                        Chain(
                                                            "<p>",
                                                            _(
                                                                "Betty was named after <a href=\"{liberta_lankester_url}\">Liberta 'Betty' Lankester</a>, and this website shows a small sample of her family history. You can browse the pages about her and some of her family to get an idea of what a Betty site looks like."
                                                            ).format(
                                                                liberta_lankester_url="betty-entity://person/betty-demo-liberta-lankester"
                                                            ),
                                                            "</p>",
                                                        ),
                                                        HTML,
                                                    ),
                                                ),
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
                            NewContentBuilder(
                                Section,
                                SectionConfig(
                                    NewContentBuilder(
                                        Columns,
                                        ColumnsConfig(
                                            [
                                                NewContentBuilder(
                                                    EntityCard,
                                                    EntityReference(
                                                        Place,
                                                        "betty-demo-amsterdam",
                                                    ),
                                                )
                                            ],
                                            [
                                                NewContentBuilder(
                                                    EntityCard,
                                                    EntityReference(
                                                        Person,
                                                        "betty-demo-liberta-lankester",
                                                    ),
                                                )
                                            ],
                                            [
                                                NewContentBuilder(
                                                    EntityCard,
                                                    EntityReference(
                                                        Place,
                                                        "betty-demo-netherlands",
                                                    ),
                                                )
                                            ],
                                            width={
                                                Breakpoint.XS: [12, 12, 12],
                                                Breakpoint.MD: [6, 6, 6],
                                                Breakpoint.LG: [4, 4, 4],
                                            },
                                        ),
                                    ),
                                    heading=_("Discover the history of a family…"),
                                ),
                            ),
                        ],
                        Region.FRONT_PAGE_SUMMARY: [
                            NewContentBuilder(
                                Render,
                                RenderConfig(
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
        license=NewLicense("spdx-gpl-3-0-or-later"),
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
            *[
                locale
                for po_file in dirs.builtin_asset_directory.glob("locale/*/betty.po")
                if (locale := Locale.parse(po_file.parent.name))
                and locale != default_locale
            ],
        ],
        name="demo",
        supported_plugins=[
            WikipediaSummary,
        ],
        title=_("A Betty demonstration"),
        url=url or "https://example.com",
    )
