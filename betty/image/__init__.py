"""
Manipulate images.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from io import BytesIO
from itertools import chain
from typing import IO, TYPE_CHECKING, Final, Self, final, overload

from PIL.Image import EXTENSION

from betty.definition import HasDefinition
from betty.definition.cls import ClsDefinition
from betty.definition.ordered import Order, OrderedDefinition
from betty.file import write
from betty.localizables.gettext import _, ngettext
from betty.media_type import MediaType, MediaTypeDefinition, MediaTypeRepository
from betty.media_types import gif, jpeg, png
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.factory import (
    ManufacturablePlugin,
    PluginManufacturer,
    PluginManufacturerDefinition,
    ResolvablePluginManufacturer,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from PIL.Image import Image

    from betty.machine_name import ResolvableMachineName
    from betty.pathlib import StrPath
    from betty.requirement import Requires

type Percentage = int
type Pixel = int
type OneDimensionalSize = tuple[Pixel, None] | tuple[None, Pixel]
type TwoDimensionalSize = tuple[Pixel, Pixel]
type Size = OneDimensionalSize | TwoDimensionalSize
type FocusArea = tuple[Percentage, Percentage, Percentage, Percentage]


class ImageReader(HasDefinition["ImageReaderDefinition"], metaclass=ABCMeta):
    """
    An image reader.
    """

    @abstractmethod
    async def read(self, image: bytes | Path, /) -> Image:
        """
        Read an image.
        """


@final
@PluginTypeDefinition(
    "image-reader",
    label=_("Image reader"),
    label_plural=_("Image readers"),
    label_countable=ngettext("{count} image reader", "{count} image readers"),
)
class ImageReaderDefinition(
    OrderedDefinition, ClsDefinition[ImageReader], PluginDefinition
):
    """
    .. plugin_type:: image-reader.
    """

    def __init__(
        self,
        id_: ResolvableMachineName,
        /,
        *,
        after: Order[Self] = (),
        before: Order[Self] = (),
        media_types: MediaTypeDefinition | Iterable[MediaTypeDefinition],
        requires: Requires = (),
    ):
        super().__init__(id_, after=after, auto=True, before=before, requires=requires)
        self.media_types: Final[Sequence[MediaTypeDefinition]] = (
            (media_types,)
            if isinstance(media_types, MediaTypeDefinition)
            else tuple(media_types)
        )


@final
@PluginManufacturerDefinition(ImageReaderDefinition)
class ImageReaderManufacturer(PluginManufacturer[ImageReaderDefinition, ImageReader]):
    """
    The image reader manufacturer.
    """


type ResolvableImageReaderManufacturer = ResolvablePluginManufacturer[
    ImageReaderDefinition, ImageReaderManufacturer
]


type ManufacturableImageReader = ManufacturablePlugin[
    ImageReaderDefinition, ImageReaderManufacturer, ImageReader
]


@final
class Imager:
    """
    The image.
    """

    def __init__(self, readers: Iterable[ImageReader], /):
        self._readers = {
            media_type.definition.id: reader
            for reader in reversed(tuple(readers))
            for media_type in reader.definition.media_types
        }
        # @todo Finish the list of publishable image types. Are there any image/* IANA media types that browsers cannot
        # @todo display (surely?)
        self.publishable: Final[MediaTypeRepository] = MediaTypeRepository(
            gif, jpeg, png
        )
        self.readable: Final[MediaTypeRepository] = MediaTypeRepository(
            *chain(
                *(reader.definition.media_types for reader in self._readers.values())
            )
        )
        self.writable: Final[MediaTypeRepository] = MediaTypeRepository(gif, jpeg, png)

    @overload
    async def read(
        self, image: StrPath, /, *, media_type: MediaTypeDefinition | None = None
    ) -> Image:
        pass

    @overload
    async def read(
        self, image: IO[bytes], /, *, media_type: MediaTypeDefinition
    ) -> Image:
        pass

    async def read(self, image, /, *, media_type=None):
        """
        Read an image.
        """
        if media_type is None:
            media_type, _extension = self.readable.extensions.require(image)
        return self._readers[media_type.id].read(image)

    async def write(
        self,
        image: Image,
        destination: Path,
        /,
        *,
        media_type: MediaType | MediaTypeDefinition,
    ) -> None:
        """
        Write an image.
        """
        image_data = BytesIO()
        image.save(
            image_data, format=EXTENSION[self.writable.require(media_type).extension]
        )
        image_data.seek(0)
        await write(destination, image_data.read(), mode="wb")
