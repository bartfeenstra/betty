"""
Provide configuration for the Wikipedia extension.
"""

from typing import Self

from typing_extensions import override

from betty.config import Configuration
from betty.serde.dump import Dump, VoidableDump, minimize, VoidableDictDump
from betty.serde.load import (
    Fields,
    OptionalField,
    AssertionChain,
    assert_record,
    assert_bool,
    assert_setattr,
)


class WikipediaConfiguration(Configuration):
    """
    Provides configuration for the :py:class:`betty.extension.wikipedia.Wikipedia` extension.
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
    def update(self, other: Self) -> None:
        self._populate_images = other._populate_images
        self._dispatch_change()

    @override
    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        assert_record(
            Fields(
                OptionalField(
                    "populate_images",
                    AssertionChain(assert_bool())
                    | assert_setattr(configuration, "populate_images"),
                ),
            )
        )(dump)
        return configuration

    @override
    def dump(self) -> VoidableDump:
        dump: VoidableDictDump[VoidableDump] = {
            "populate_images": self.populate_images,
        }
        return minimize(dump, True)
