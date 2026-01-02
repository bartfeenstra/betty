"""
Provide Betty's ancestry source types.
"""

from __future__ import annotations

from typing import final

from betty.ancestry.source_type import SourceType, SourceTypeDefinition
from betty.classtools import Singleton
from betty.locale.localizable.gettext import _, ngettext


@final
@SourceTypeDefinition(
    "archive",
    label=_("Archive"),
    label_plural=_("Archives"),
    label_countable=ngettext("{count} archive", "{count} archives"),
)
class Archive(SourceType):
    """
    A archive.
    """


@final
@SourceTypeDefinition(
    "book",
    label=_("Book"),
    label_plural=_("Books"),
    label_countable=ngettext("{count} book", "{count} books"),
)
class Book(SourceType):
    """
    A book.
    """

@final
@SourceTypeDefinition(
    "unknown",
    label=_("Unknown"),
    label_plural=_("Unknowns"),
    label_countable=ngettext("{count} unknown", "{count} unknowns"),
)
class Unknown(SourceType, Singleton):
    """
    A source of an unknown type.
    """

@final
@SourceTypeDefinition(
    "website",
    label=_("Website"),
    label_plural=_("Websites"),
    label_countable=ngettext("{count} website", "{count} websites"),
)
class Website(SourceType):
    """
    A website.
    """
