from typing import Self

import pytest

from betty.capability import (
    Capable,
    Incapable,
    NotYetInitialized,
    ResolvableStagedCapability,
    Stage,
    UnsupportedCapability,
)


class _Stage(Stage):
    pass


class _Capability:
    pass


class _Capable(Capable[_Stage]):
    def __init__(
        self,
        my_first_capability: ResolvableStagedCapability[Self, _Capability, _Stage]
        | None = None,
        /,
    ):
        super().__init__(
            capabilities={
                "my_first_capability": (_Capability, my_first_capability),
            }
        )

    def init_staged_capabilities(self) -> None:
        self._init_staged_capabilities(_Stage)


class TestUnsupportedCapability:
    def test(self) -> None:
        assert (
            str(UnsupportedCapability(Capable(), "my_first_capability"))
            == 'betty.capability:Capable does not support the "my_first_capability" capability.'
        )


class TestIncapable:
    def test(self) -> None:
        assert (
            str(Incapable(Capable(), "my_first_capability"))
            == 'betty.capability:Capable does not have a(n) "my_first_capability" capability.'
        )


class TestNotYetInitialized:
    def test(self) -> None:
        assert (
            str(NotYetInitialized(Capable(), "my_first_capability", _Stage))
            == 'betty.capability:Capable\'s "my_first_capability" capability was not yet initialized for stage betty.tests.test_capability:_Stage.'
        )


class TestCapable:
    def test__capability__with_unsupported_capability(self) -> None:
        sut = Capable()
        with pytest.raises(UnsupportedCapability):
            sut._capability("my_first_capability")

    def test__capability__with_incapable(self) -> None:
        sut = _Capable()
        with pytest.raises(Incapable):
            sut._capability("my_first_capability")

    def test__capability__with_uninitialized_staged_capability_manufacturer(
        self,
    ) -> None:
        capability = _Capability()
        sut = _Capable(_Stage(lambda _: capability))
        with pytest.raises(NotYetInitialized):
            sut._capability("my_first_capability")

    def test__capability__with_initialized_staged_capability_manufacturer(self) -> None:
        capability = _Capability()
        sut = _Capable(_Stage(lambda _: capability))
        sut.init_staged_capabilities()
        assert sut._capability("my_first_capability") is capability

    def test__capability__with_capability_manufacturer(self) -> None:
        capability = _Capability()
        sut = _Capable(lambda _: capability)
        assert sut._capability("my_first_capability") is capability

    def test__capability__with_capability(self) -> None:
        capability = _Capability()
        sut = _Capable(capability)
        assert sut._capability("my_first_capability") is capability

    def test__try_capability__with_unsupported_capability(self) -> None:
        sut = Capable()
        with pytest.raises(UnsupportedCapability):
            sut._try_capability("my_first_capability")

    def test__try_capability__with_incapable(self) -> None:
        sut = _Capable()
        assert sut._try_capability("my_first_capability") is None

    def test__try_capability__with_uninitialized_staged_capability_manufacturer(
        self,
    ) -> None:
        capability = _Capability()
        sut = _Capable(_Stage(lambda _: capability))
        with pytest.raises(NotYetInitialized):
            sut._try_capability("my_first_capability")

    def test__try_capability__with_initialized_staged_capability_manufacturer(
        self,
    ) -> None:
        capability = _Capability()
        sut = _Capable(_Stage(lambda _: capability))
        sut.init_staged_capabilities()
        assert sut._try_capability("my_first_capability") is capability

    def test__try_capability__with_capability_manufacturer(self) -> None:
        capability = _Capability()
        sut = _Capable(lambda _: capability)
        assert sut._try_capability("my_first_capability") is capability

    def test__try_capability__with_capability(self) -> None:
        capability = _Capability()
        sut = _Capable(capability)
        assert sut._try_capability("my_first_capability") is capability
