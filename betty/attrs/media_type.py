"""
Media type attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attrs.owner import OwnerAttr
from betty.classtools.init import Init
from betty.data import DataDefinition
from betty.datas.aggregate.record import FieldDefinition
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.attrs.common import OptionableCommonAttr
    from betty.content_type import ContentTypeDefinition
    from betty.localizer import AnyLocalizable


# @todo Make an inventory of where and how we use this. Then refactor.
def new_media_type_attr(
    *, label: AnyLocalizable | None = None, description: AnyLocalizable | None = None
) -> OptionableCommonAttr[Init, ContentTypeDefinition, ContentTypeDefinition]:
    """
    Create an attribute containing a media type.
    """
    return OwnerAttr(
        FieldDefinition(
            DataDefinition(label=_("Media type")),
            label=label,
            description=description,
        )
    )


class HasMediaType(Init):
    """
    A resource with an `IANA media type <https://www.iana.org/assignments/media-types/media-types.xhtml>`_.
    """

    media_type = new_media_type_attr().optional

    def __init__(
        self,
        *args: Any,
        media_type: ContentTypeDefinition | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.media_type = media_type
