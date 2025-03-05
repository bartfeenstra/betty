from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    label = "Hit me, I am a button!"
    async with assert_template_file(
        data={
            "button_label": label,
        },
        extensions={RaspberryMint},
        template="component/submit.html.j2",
    ) as (actual, _):
        assert "<input " in actual
        assert 'type="submit"' in actual
        assert "btn-primary" in actual
        assert label in actual


async def test_secondary() -> None:
    async with assert_template_file(
        data={
            "button_label": "Hit me, I am a button!",
            "button_secondary": True,
        },
        extensions={RaspberryMint},
        template="component/submit.html.j2",
    ) as (actual, _):
        assert "btn-secondary" in actual


async def test_with_html_id() -> None:
    html_id = "my-first-id"
    async with assert_template_file(
        data={
            "button_label": "Hit me, I am a button!",
            "html_id": html_id,
        },
        extensions={RaspberryMint},
        template="component/submit.html.j2",
    ) as (actual, _):
        assert f'id="{html_id}"' in actual


async def test_with_html_class() -> None:
    html_class = "my-first-class"
    async with assert_template_file(
        data={
            "button_label": "Hit me, I am a button!",
            "html_class": [html_class],
        },
        extensions={RaspberryMint},
        template="component/submit.html.j2",
    ) as (actual, _):
        assert html_class in actual
