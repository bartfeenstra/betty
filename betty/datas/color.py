"""
Color data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty import samples
from betty.data import DataDefinition
from betty.localizables.gettext import _
from betty.localizables.markup import Quote
from betty.porters.callback import CallbackPorter
from betty.sample import Sample, Samples
from betty.validators.color import is_hex
from betty.validators.str import is_str

if TYPE_CHECKING:
    from betty.localizable import ResolvableLocalizable


@final
class ColorDefinition(DataDefinition[str]):
    """
    Define a color.
    """

    def __init__(self, *, label: ResolvableLocalizable | None = None):
        super().__init__(
            label=label or _("Color"),
            description=_("A hexadecimal color, such as {example_color}").format(
                example_color=Quote(samples.color_hex)
            ),
            samples=Samples(lambda: Sample("#ff0000", label="Default")),
            porter=CallbackPorter[str](is_str | is_hex, str),
        )
