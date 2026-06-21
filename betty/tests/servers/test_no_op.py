from urllib.parse import urlparse

from betty.servers.no_op import NoOpServer


class TestNoOpServer:
    async def test_start(self) -> None:
        await NoOpServer().start()

    async def test_stop(self) -> None:
        await NoOpServer().stop()

    async def test_public_url(self) -> None:
        sut = NoOpServer()
        assert sut.public_url
        assert urlparse(sut.public_url)

    async def test_show(self) -> None:
        await NoOpServer().show()
