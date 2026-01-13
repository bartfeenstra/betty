"""
Configuration for the Wikipedia extension.
"""

from collections.abc import Iterable
from typing import Any, Self

from typing_extensions import override

from betty.assertion import (
    OptionalField,
    assert_bool,
    assert_record,
)
from betty.config import Configuration, Sample
from betty.serde import SerializedData, SerializedMapping


class WikiConfiguration(Configuration):
    """
    Configuration for the :py:class:`betty.project.extension.wiki.Wiki` extension.

    .. configuration:: betty.project.extension.wiki.config:WikiConfiguration

    ``populate_images``
    ^^^^^^^^^^^^^^^^^^^
    :sup:`optional`

    A boolean indicating whether to download images from the Wikipedia links in the ancestry. Defaults to ``true``.
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
    def load(cls, serialized: SerializedData, /) -> Self:
        return cls(
            **assert_record(OptionalField("populate_images", assert_bool))(serialized)
        )

    @override
    def dump(self) -> SerializedMapping[SerializedData]:
        return {
            "populate_images": self.populate_images,
        }

    @override
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.populate_images == other.populate_images

    @override
    @classmethod
    def samples(cls) -> Iterable[Sample[Self]]:
        yield Sample(cls(), label="Default")
