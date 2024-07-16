from json import dumps

from multidict import CIMultiDict

from betty.fetch import FetchResponse


class TestFetchError:
    pass


class TestFetchResponse:
    async def test_json(self) -> None:
        json_data = {
            "Hello": "World!",
        }
        sut = FetchResponse(CIMultiDict(), dumps(json_data).encode("utf-8"), "utf-8")
        assert sut.json == json_data

    async def test_text(self) -> None:
        text = "Hello, world!"
        sut = FetchResponse(CIMultiDict(), text.encode("utf-8"), "utf-8")
        assert sut.text == text
