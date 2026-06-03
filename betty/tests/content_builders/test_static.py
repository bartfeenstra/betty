from betty.content_builders.static import Static
from betty.document import Document


class TestStatic:
    async def test_build__without_content(self) -> None:
        assert await Static().build(document=Document()) is None

    async def test_build__with_content(self) -> None:
        content = "Hello, world!"
        assert await Static(content).build(document=Document()) == content
