from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.linked_data import LinkedDataDumpableWithSchema

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertTemplateString


class TestLinkedDataDumpable:
    @pytest.mark.parametrize(
        ("expected", "data"),
        [
            ("true", LinkedDataDumpableWithSchema()),
            ("false", LinkedDataDumpableWithSchema),
            ("false", object()),
        ],
    )
    async def test___call__(
        self, assert_template_string: AssertTemplateString, expected: str, data: Any
    ) -> None:
        template = "{% if data is linked_data_dumpable %}true{% else %}false{% endif %}"
        async with assert_template_string(
            template=template,
            data={
                "data": data,
            },
        ) as (actual, _):
            assert actual == expected
