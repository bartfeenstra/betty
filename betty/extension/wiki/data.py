"""
Data for the Wikipedia extension.
"""

from typing import final

from betty.data import Data, Sample
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.bool import BoolDefinition
from betty.locale.localizable.gettext import _
from betty.property import Optional, Property
from betty.sample import Size


@final
@ObjectDefinition(
    label=_("Wiki extension configuration"),
    samples=[
        lambda: Sample(WikiConfiguration(), label="Minimal", size=Size.MINIMAL),
        lambda: Sample(
            WikiConfiguration(populate_images=False), label="Full", size=Size.FULL
        ),
    ],
)
class WikiConfiguration(Data):
    """
    Configuration for the :py:class:`betty.extension.wiki.Wiki` extension.

    .. data:: betty.extension.wiki.data:WikiConfiguration
    """

    populate_images = Optional(
        Property(
            BoolDefinition(
                label=_("Populate images"),
                description=_(
                    "Whether to download additional images found through Wikipedia links in the ancestry"
                ),
            ),
            omit_load=True,
            omit_dump=lambda data: data is True,
        )
    )
    """
    Whether to populate entities with Wikimedia images after loading ancestries.
    """

    def __init__(self, *, populate_images: bool = True):
        self.populate_images = populate_images
