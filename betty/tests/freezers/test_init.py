from typing import override

import pytest

from betty.freezers.init import FrozenOnInit
from betty.frozen import is_frozen


class TestFrozenOnInit:
    def test__is_frozen(self) -> None:
        assert is_frozen(FrozenOnInit())

    def test_is_frozen(self) -> None:
        assert FrozenOnInit().is_frozen

    def test_post_init(self) -> None:
        class _Sut(FrozenOnInit):
            @override
            def freeze(self) -> None:
                raise RuntimeError

        with pytest.raises(RuntimeError):
            _Sut()
