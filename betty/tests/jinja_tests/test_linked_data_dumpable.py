from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.linked_data import LinkedDataDumpableWithSchemaJsonLdObject

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertJinja


class TestLinkedDataDumpable:
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", LinkedDataDumpableWithSchemaJsonLdObject()),
            ("false", LinkedDataDumpableWithSchemaJsonLdObject),
            ("false", object()),
        ],
    )
    async def test___call__(
        self, assert_jinja_str: AssertJinja, expected: str, data: Any
    ) -> None:
        template = "{% if data is linked_data_dumpable %}true{% else %}false{% endif %}"
        async with assert_jinja_str(template, data={"data": data}) as rendered:
            assert rendered == expected
