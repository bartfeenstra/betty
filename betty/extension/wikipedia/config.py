"""
Provide configuration for the Wikipedia extension.
"""

from typing import Self

from betty.config import Configuration
from betty.serde.dump import Dump, VoidableDump, minimize, VoidableDictDump
from betty.serde.load import Asserter, Fields, OptionalField, Assertions


class WikipediaConfiguration(Configuration):
    def __init__(self):
        super().__init__()
        self._populate_images = True

    @property
    def populate_images(self) -> bool:
        return self._populate_images

    @populate_images.setter
    def populate_images(self, populate_images: bool) -> None:
        self._populate_images = populate_images

    def update(self, other: Self) -> None:
        self._populate_images = other._populate_images
        self._dispatch_change()

    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter()
        asserter.assert_record(
            Fields(
                OptionalField(
                    "populate_images",
                    Assertions(asserter.assert_bool())
                    | asserter.assert_setattr(configuration, "populate_images"),
                ),
            )
        )(dump)
        return configuration

    def dump(self) -> VoidableDump:
        dump: VoidableDictDump[VoidableDump] = {
            "populate_images": self.populate_images,
        }
        return minimize(dump, True)
