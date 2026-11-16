from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    url = "https://example.com/per/ma.link"
    async with assert_raspberry_mint_jinja_file(
        "component/permalink.html.j2", data={"url": url}
    ) as rendered:
        assert "<a " in rendered
        assert url in rendered
