"""
Provide configuration for the Wikipedia extension.
"""

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    assert_record,
    assert_bool,
    assert_setattr,
)
from betty.config import Configuration
from betty.serde.dump import Dump, DumpMapping


class WikipediaConfiguration(Configuration):
    """
    Provides configuration for the :py:class:`betty.project.extension.wikipedia.Wikipedia` extension.
    """

    def __init__(self):
        super().__init__()
        self._populate_images = True

    @property
    def populate_images(self) -> bool:
        """
        Whether to populate entities with Wikimedia images after loading ancestries.
        """
        return self._populate_images

    @populate_images.setter
    def populate_images(self, populate_images: bool) -> None:
        self._populate_images = populate_images

    @override
    def load(self, dump: Dump) -> None:
        assert_record(
            OptionalField(
                "populate_images",
                assert_bool() | assert_setattr(self, "populate_images"),
            )
        )(dump)

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "populate_images": self.populate_images,
        }
