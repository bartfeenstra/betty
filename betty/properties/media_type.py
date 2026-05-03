"""
Media type properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.media_type import MediaType, ResolvableMediaType, resolve_media_type
from betty.property import Property

if TYPE_CHECKING:
    from collections.abc import Callable

    from betty.locale.localizable import ResolvableLocalizable


@final
class MediaTypeProperty(Property[MediaType, ResolvableMediaType]):
    """
    A property containing a media type.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable | None = None,
        default: Callable[[], MediaType] | None = None,
        description: ResolvableLocalizable | None = None,
        omit_load: bool | None = None,
        omit_dump: Callable[[MediaType], bool] | None = None,
    ):
        super().__init__(
            data=MediaType,
            default=default,
            label=label,
            description=description,
            omit_load=omit_load,
            omit_dump=omit_dump,
            resolver=resolve_media_type,
        )
