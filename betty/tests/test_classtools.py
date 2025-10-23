from betty.classtools import Singleton


class TestSingleton:
    def test___new__(self) -> None:
        assert Singleton() is Singleton()
