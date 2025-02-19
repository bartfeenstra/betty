from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "component/submit.html.j2"

    async def test_minimal(self) -> None:
        label = "Hit me, I am a button!"
        async with self.assert_template_file(
            data={
                "button_label": label,
            }
        ) as (actual, _):
            assert "<input " in actual
            assert 'type="submit"' in actual
            assert "btn-primary" in actual
            assert label in actual

    async def test_secondary(self) -> None:
        async with self.assert_template_file(
            data={
                "button_label": "Hit me, I am a button!",
                "button_secondary": True,
            }
        ) as (actual, _):
            assert "btn-secondary" in actual

    async def test_with_html_id(self) -> None:
        html_id = "my-first-id"
        async with self.assert_template_file(
            data={
                "button_label": "Hit me, I am a button!",
                "html_id": html_id,
            }
        ) as (actual, _):
            assert f'id="{html_id}"' in actual

    async def test_with_html_class(self) -> None:
        html_class = "my-first-class"
        async with self.assert_template_file(
            data={
                "button_label": "Hit me, I am a button!",
                "html_class": [html_class],
            }
        ) as (actual, _):
            assert html_class in actual
