"""
Localizable data.
"""

from __future__ import annotations

from typing import TypeVar, final

from betty.classtools import Singleton
from betty.data import DataDefinition
from betty.locale.localizable import CountableLocalizable, Localizable
from betty.locale.localizable.gettext import _
from betty.locale.localizable.portable import (
    dump_countable_localizable,
    dump_localizable,
    load_countable_localizable,
    load_localizable,
)
from betty.portable import CallbackPorter

_DataT = TypeVar("_DataT")


@final
class LocalizableDefinition(DataDefinition[Localizable], Singleton):
    """
    The data definition for :py:class:`betty.locale.localizable.Localizable`.
    """

    def __init__(self):
        super().__init__(
            cls=Localizable,
            label=_("A localizable string"),
            porter=CallbackPorter(load_localizable, dump_localizable),
        )


@final
class CountableLocalizableDefinition(DataDefinition[CountableLocalizable], Singleton):
    """
    The data definition for :py:class:`betty.locale.localizable.CountableLocalizable`.
    """

    def __init__(self):
        super().__init__(
            cls=CountableLocalizable,
            label=_("A countable localizable string"),
            porter=CallbackPorter(
                load_countable_localizable, dump_countable_localizable
            ),
        )
