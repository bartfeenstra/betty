from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "component/checkbox.html.j2"

    async def test_minimal(self) -> None:
        label = "Check me out!"
        value = "Look at this treasure"
        async with self.assert_template_file(
            data={
                "checkbox_label": label,
                "checkbox_value": value,
            }
        ) as (actual, _):
            assert "<input" in actual
            assert 'type="checkbox"' in actual
            assert label in actual
            assert value in actual

    async def test_with_html_id(self) -> None:
        html_id = "my-first-id"
        async with self.assert_template_file(
            data={
                "checkbox_label": "Check me out!",
                "html_id": html_id,
            }
        ) as (actual, _):
            assert f'id="{html_id}"' in actual

    async def test_with_html_class(self) -> None:
        html_class = "my-first-class"
        async with self.assert_template_file(
            data={
                "checkbox_label": "Check me out!",
                "html_class": [html_class],
            }
        ) as (actual, _):
            assert html_class in actual

    async def test_with_checkbox_checked(self) -> None:
        async with self.assert_template_file(
            data={
                "checkbox_label": "Check me out!",
                "checkbox_checked": True,
            }
        ) as (actual, _):
            assert " checked" in actual
