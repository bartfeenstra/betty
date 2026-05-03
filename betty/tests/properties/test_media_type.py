from __future__ import annotations

from betty.media_type import MediaType, MediaTypeDefinition
from betty.properties.media_type import MediaTypeProperty


class TestMediaTypeProperty:
    def test_resolve(self) -> None:
        class Cls:
            media_type = MediaTypeProperty()

        instance = Cls()
        media_type = MediaType("text/plain")
        instance.media_type = MediaTypeDefinition("-", label="-", media_type=media_type)
        assert instance.media_type is media_type
