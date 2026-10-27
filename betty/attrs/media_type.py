"""
Media type attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attrs.owner import OwnerAttr
from betty.classtools import TypeABCMeta
from betty.datas.aggregate.record import FieldDefinition
from betty.media_type import MediaType, ResolvableMediaType, resolve_media_type
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.attrs.common import OptionableCommonAttr
    from betty.localizable import ResolvableLocalizable


def new_media_type_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> OptionableCommonAttr[HasProps, MediaType, ResolvableMediaType]:
    """
    Create an attribute containing a media type.
    """
    return OwnerAttr(
        FieldDefinition(MediaType, label=label, description=description)
    ).setter(resolve_media_type)


class HasMediaType(HasProps, metaclass=TypeABCMeta):
    """
    A resource with an `IANA media type <https://www.iana.org/assignments/media-types/media-types.xhtml>`_.
    """

    media_type = new_media_type_attr().optional

    def __init__(
        self,
        *args: Any,
        media_type: ResolvableMediaType | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.media_type = media_type
