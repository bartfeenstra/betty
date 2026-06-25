from betty.porters.callback import CallbackPorter


class TestCallbackPorter:
    def test_load(self) -> None:
        sut = CallbackPorter(lambda _: "loaded", lambda _: "dumped")
        assert sut.load(None) == "loaded"

    def test_dump(self) -> None:
        sut = CallbackPorter(lambda _: None, lambda _: "dumped")
        assert sut.dump(None) == "dumped"
