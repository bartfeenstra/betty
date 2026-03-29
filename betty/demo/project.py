"""
Create demonstration projects.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from betty.content import ContentManufacturer
from betty.entity.reference import EntityReference
from betty.extension import ExtensionManufacturer
from betty.license import LicenseManufacturer
from betty.locale import DEFAULT_LOCALE
from betty.locale.localizable.gettext import _
from betty.locale.localizable.markup import Chain
from betty.locale.localize import LocalizerRepository
from betty.media_type.media_types import HTML
from betty.plugins.content.raspberry_mint_columns import Columns, ColumnsConfiguration
from betty.plugins.content.raspberry_mint_entity_card import EntityCard
from betty.plugins.content.raspberry_mint_incomplete_translation_warning import (
    IncompleteTranslationWarning,
)
from betty.plugins.content.raspberry_mint_section import Section, SectionConfiguration
from betty.plugins.content.render import Render, RenderConfiguration
from betty.plugins.content.wikipedia_summary import WikipediaSummary
from betty.plugins.enricher.deriver import Deriver
from betty.plugins.enricher.wiki import Wiki
from betty.plugins.entity.event import Event
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.entity.source import Source
from betty.plugins.extension.http_api_doc import HttpApiDoc
from betty.plugins.extension.maps import Maps
from betty.plugins.extension.raspberry_mint import (
    Breakpoint,
    RaspberryMint,
    RaspberryMintConfiguration,
    Region,
)
from betty.plugins.extension.raspberry_mint.default import regional_content
from betty.plugins.extension.spdx import Spdx
from betty.plugins.extension.trees import Trees
from betty.plugins.link.betty_documentation import BettyDocumentation
from betty.plugins.link.betty_github import BettyGithub
from betty.plugins.loader.demo import Demo
from betty.project import Project

if TYPE_CHECKING:
    from pathlib import Path

    from betty.app import App


async def create_project(
    app: App, directory: Path, *, url: str | None = None
) -> Project:
    """
    Create a new demonstration project.
    """
    translations = await app.translations
    localizer_repository = LocalizerRepository(translations)
    localizers = [localizer_repository.get(locale) for locale in translations.locales]

    return Project(
        app=app,
        directory=directory,
        name="demo",
        license=LicenseManufacturer("spdx-gpl-3--0-or-later"),
        title=_("A Betty demonstration"),
        author=_("Bart Feenstra and contributors"),
        url=url or "https://example.com",
        service_plugins=[
            BettyDocumentation,
            BettyGithub,
            Demo,
            Deriver,
            HttpApiDoc,
            Maps,
            RaspberryMint,
            Spdx,
            ExtensionManufacturer(
                RaspberryMint,
                RaspberryMintConfiguration(
                    regional_content={
                        **regional_content(localizers=localizers),
                        Region.FRONT_PAGE_CONTENT: [
                            ContentManufacturer(
                                Columns,
                                ColumnsConfiguration([[IncompleteTranslationWarning]]),
                            ),
                            ContentManufacturer(
                                Section,
                                SectionConfiguration(
                                    ContentManufacturer(
                                        Columns,
                                        ColumnsConfiguration(
                                            [
                                                [
                                                    ContentManufacturer(
                                                        Render,
                                                        RenderConfiguration(
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
                                                    ContentManufacturer(
                                                        Render,
                                                        RenderConfiguration(
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
                            ContentManufacturer(
                                Section,
                                SectionConfiguration(
                                    ContentManufacturer(
                                        Columns,
                                        ColumnsConfiguration(
                                            [
                                                [
                                                    ContentManufacturer(
                                                        EntityCard,
                                                        EntityReference(
                                                            Place,
                                                            "betty-demo-amsterdam",
                                                        ),
                                                    )
                                                ],
                                                [
                                                    ContentManufacturer(
                                                        EntityCard,
                                                        EntityReference(
                                                            Person,
                                                            "betty-demo-liberta-lankester",
                                                        ),
                                                    )
                                                ],
                                                [
                                                    ContentManufacturer(
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
                            ContentManufacturer(
                                Render,
                                RenderConfiguration(
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
            Wiki,
        ],
        support_plugins=[
            WikipediaSummary,
        ],
        entity_types=[
            Person,
            Event,
            Place,
            Source,
        ],
        locales=[
            # The first configured locale is the project default.
            DEFAULT_LOCALE,
            *[locale for locale in translations.locales if locale != DEFAULT_LOCALE],
        ],
    )
