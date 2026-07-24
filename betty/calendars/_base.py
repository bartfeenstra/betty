from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.calendar import Calendar

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.localizable import Localizable
    from betty.machine_name import MachineName


class _CalendarBase(Calendar):
    _id: MachineName
    _label: Localizable
    _public_label: Localizable
    _years: Sequence[int]

    @final
    @override
    @classmethod
    def id(cls) -> MachineName:
        return cls._id

    @final
    @override
    @classmethod
    def label(cls) -> Localizable:
        return cls._label

    @final
    @override
    @classmethod
    def public_label(cls) -> Localizable:
        return cls._public_label

    @final
    @override
    @classmethod
    def years(cls) -> Sequence[int]:
        return cls._years
