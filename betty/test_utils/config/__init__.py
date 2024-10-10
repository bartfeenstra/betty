"""
Test utilities for :py:mod:`betty.config`.
"""

from typing import Self

from typing_extensions import override

from betty.config import Configuration
from betty.serde.dump import Dump


class DummyConfiguration(Configuration):
    """
    A dummy :py:class:`betty.config.Configuration` implementation.
    """

    @override
    def update(self, other: Self) -> None:
        pass  # pragma: no cover

    @override
    def load(self, dump: Dump) -> None:
        pass  # pragma: no cover

    @override
    def dump(self) -> Dump:
        return None  # pragma: nocover
