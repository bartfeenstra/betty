from __future__ import annotations

from typing import Any

import pytest

from betty.json.linked_data import LinkedDataDumpableWithSchemaJsonLdObject
from betty.test_utils.jinja import assert_template_string


class TestLinkedDataDumpable:
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", LinkedDataDumpableWithSchemaJsonLdObject()),
            ("false", LinkedDataDumpableWithSchemaJsonLdObject),
            ("false", object()),
        ],
    )
    async def test___call__(self, expected: str, data: Any) -> None:
        template = "{% if data is linked_data_dumpable %}true{% else %}false{% endif %}"
        async with assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected
