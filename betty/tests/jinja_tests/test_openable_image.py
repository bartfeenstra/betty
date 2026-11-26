from __future__ import annotations

from typing import TYPE_CHECKING

from betty.content_types import plain_text, png

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertJinja


class TestOpenableImage:
    async def test___call__(self, assert_jinja_str: AssertJinja) -> None:
        template = """
{% for data in datas %}
    {% if data is openable_image %}true{% else %}false{% endif %}
{% endfor %}
"""
        async with assert_jinja_str(
            template, data={"datas": [png, plain_text]}
        ) as rendered:
            assert rendered == "\ntruefalse"
