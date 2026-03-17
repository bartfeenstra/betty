from betty.document import Document
from betty.plugins.content.static import Static


class TestStatic:
    async def test_build__without_content(self) -> None:
        assert await Static().build(document=Document()) is None

    async def test_build__with_content(self) -> None:
        content = "Hello, world!"
        assert await Static(content).build(document=Document()) == content
