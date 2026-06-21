from __future__ import annotations

from betty.exception import HumanFacingException
from betty.localizables.static import StaticTranslations


def _always_valid(value: int) -> int:
    return value


def _always_invalid(value: int) -> int:
    raise HumanFacingException(StaticTranslations(""))
