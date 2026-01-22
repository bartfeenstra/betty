"""
Configuration for the Wikipedia extension.
"""

from typing import final

from betty.data import Data, Sample
from betty.data.aggregate.record import FieldDefinition
from betty.data.aggregate.record.object import ObjectDefinition
from betty.data.indicator.selector import Attr
from betty.data.simple import SimpleDefinition
from betty.locale.localizable.gettext import _


@final
@ObjectDefinition(
    label=_("Wiki extension configuration"),
    fields=[
        FieldDefinition(
            Attr("populate_images"),
            SimpleDefinition(
                cls=bool,
                label=_("Populate images"),
                description=_(
                    "Whether to download additional images found through Wikipedia links in the ancestry"
                ),
                empty=lambda data: data is True,
            ),
            required=False,
        )
    ],
    samples=[
        lambda: Sample(WikiConfiguration(), label="Minimal", minimal=True),
        lambda: Sample(
            WikiConfiguration(populate_images=False), label="Full", full=True
        ),
    ],
)
class WikiConfiguration(Data):
    """
    Configuration for the :py:class:`betty.project.extension.wiki.Wiki` extension.

    .. data:: betty.project.extension.wiki.config:WikiConfiguration
    """

    def __init__(self, *, populate_images: bool = True):
        self._populate_images = populate_images

    @property
    def populate_images(self) -> bool:
        """
        Whether to populate entities with Wikimedia images after loading ancestries.
        """
        return self._populate_images

    @populate_images.setter
    def populate_images(self, populate_images: bool) -> None:
        self._populate_images = populate_images
