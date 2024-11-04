from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint}
    template = "component/checkboxes.html.j2"

    async def test_minimal(self) -> None:
        label = "Check these out!"
        async with self.assert_template_file(
            data={
                "checkboxes": [],
                "checkboxes_label": label,
            }
        ) as (actual, _):
            assert label in actual

    async def test_with_checkboxes_label_visually_hidden(self) -> None:
        async with self.assert_template_file(
            data={
                "checkboxes": [],
                "checkboxes_label": "Check these out!",
                "checkboxes_label_visually_hidden": True,
            }
        ) as (actual, _):
            assert "visually-hidden" in actual

    async def test_with_minimal_items(self) -> None:
        label = "Check me out!"
        value = "Look at this treasure"
        async with self.assert_template_file(
            data={
                "checkboxes": [
                    {
                        "label": label,
                        "value": value,
                    }
                ],
                "checkboxes_label": "Check these out!",
            }
        ) as (actual, _):
            assert label in actual

    async def test_with_full_items(self) -> None:
        html_class = "my-first-class"
        html_id = "my-first-id"
        async with self.assert_template_file(
            data={
                "checkboxes": [
                    {
                        "label": "Check me out!",
                        "value": "Look at this treasure",
                        "class": [html_class],
                        "id": html_id,
                    }
                ],
                "checkboxes_label": "Check these out!",
            }
        ) as (actual, _):
            assert html_class in actual
            assert f'id="{html_id}"' in actual
