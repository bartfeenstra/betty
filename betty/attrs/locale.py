"""
Locale attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from betty.attrs.owner import OwnerAttr
from betty.classtools import TypeABCMeta
from betty.datas.locale import LocaleDefinition
from betty.locale import ResolvableLocale, resolve_locale
from betty.localized import Localized
from betty.prop import HasProps

if TYPE_CHECKING:
    from babel import Locale

    from betty.attrs.common import OptionableCommonAttr
    from betty.localizable import ResolvableLocalizable


def new_locale_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
    frozen: bool = False,
) -> OptionableCommonAttr[HasProps, Locale, ResolvableLocale]:
    """
    Create an attribute containing a locale.
    """
    return OwnerAttr(
        LocaleDefinition(label=label, description=description), frozen=frozen
    ).setter(resolve_locale)


class HasLocale(Localized, HasProps, metaclass=TypeABCMeta):
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    locale = new_locale_attr().optional

    def __init__(
        self, *args: Any, locale: ResolvableLocale | None = None, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.locale = locale
