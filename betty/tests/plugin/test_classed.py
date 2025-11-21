from __future__ import annotations

from betty.plugin.classed import ClassedPluginDefinition


class TestClassedPluginDefinition:
    def test_cls(self) -> None:
        class _Cls:
            pass

        sut = ClassedPluginDefinition(cls=_Cls, id="my-first-plugin")
        assert sut.cls is _Cls

    def test___call__(self) -> None:
        class _Cls:
            pass

        sut = ClassedPluginDefinition[_Cls](id="my-first-plugin")
        sut(_Cls)
        assert sut.cls is _Cls
