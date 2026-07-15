"""
Locale data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from babel import Locale

from betty import samples
from betty.assertions.locale import assert_locale
from betty.data import DataDefinition
from betty.locale import to_language_tag
from betty.localizables.gettext import _
from betty.localizables.markup import Paragraph
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class LocaleDefinition(DataDefinition[Locale]):
    """
    Define a locale (identifier).
    """

    def __init__(
        self,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
    ):
        _description = _(
            "An IETF BCP 47 language tag, such as {example_language_tag}."
        ).format(example_language_tag=samples.language_tag)
        if description:
            _description = Paragraph(description, _description)
        super().__init__(
            cls=Locale,
            label=label or _("Locale"),
            description=_description,
            porter=CallbackPorter[Locale](assert_locale(), to_language_tag),
        )
