"""
Provide configuration for the Wikipedia extension.
"""

from typing import Self

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    assert_bool,
    assert_record,
)
from betty.config import Configuration
from betty.serde.dump import Dump, DumpMapping


class WikiConfiguration(Configuration):
    """
    Provides configuration for the :py:class:`betty.project.extension.wiki.Wiki` extension.
    """

    def __init__(self, *, populate_images: bool = True):
        super().__init__()
        self._populate_images = populate_images

    @property
    def populate_images(self) -> bool:
        """
        Whether to populate entities with Wikimedia images after loading ancestries.
        """
        return self._populate_images

    @populate_images.setter
    def populate_images(self, populate_images: bool) -> None:
        self.assert_mutable()
        self._populate_images = populate_images

    @override
    @classmethod
    def load(cls, dump: Dump, /) -> Self:
        return cls(
            **assert_record(OptionalField("populate_images", assert_bool()))(dump)
        )

    @override
    def dump(self) -> DumpMapping[Dump]:
        return {
            "populate_images": self.populate_images,
        }
