"""
Complex/markup localizables.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from textwrap import indent
from typing import TYPE_CHECKING, ClassVar, final

from typing_extensions import override

from betty.locale import HasLocale, HasLocaleStr
from betty.locale.localizable import Localizable, LocalizableLike
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.locale.localize import Localizer


class LocalizableSequence(ABC):
    """
    A sequence of localizables.
    """

    @property
    @abstractmethod
    def localizables(self) -> Sequence[Localizable]:
        """
        The localizables.
        """


class _LocalizableSequence(LocalizableSequence):
    def __init__(self, *localizables: LocalizableLike):
        self._localizables = tuple(map(ensure_localizable, localizables))

    @override
    @property
    def localizables(self) -> Sequence[Localizable]:
        return self._localizables


class _Join(_LocalizableSequence, Localizable):
    _SEPARATOR: ClassVar[str]

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        return HasLocaleStr(
            self._SEPARATOR.join(
                localized
                for part in self.localizables
                if (localized := part.localize(localizer))
            ),
            locale=localizer.locale,
        )


@final
class Chain(_Join):
    """
    Chain multiple localizables together, back to back.
    """

    _SEPARATOR = ""


@final
class Paragraph(_Join):
    """
    Represent multiple localizables as a single paragraph of text.
    """

    _SEPARATOR = " "


@final
class Lines(_Join):
    """
    Represent multiple localizables as multiple lines of text.
    """

    _SEPARATOR = "\n"


@final
class Paragraphs(_Join):
    """
    Represent multiple localizables as multiple paragraphs of text.
    """

    _SEPARATOR = "\n\n"


class _List(_LocalizableSequence, Localizable):
    _TEMPLATE_LEFT_TO_RIGHT = "{prefix} {localized}"
    _TEMPLATE_RIGHT_TO_LEFT = "{localized} {prefix}"

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        if not self.localizables:
            return HasLocaleStr("")
        localizeds = []
        prefixes = []
        prefix_lengths = []
        if localizer.locale.character_order == "right-to-left":
            template = self._TEMPLATE_RIGHT_TO_LEFT
        else:
            template = self._TEMPLATE_LEFT_TO_RIGHT
        for index, localizable in enumerate(self._localizables):
            localizeds.append(localizable.localize(localizer))
            prefix = self._get_prefix(localizer, index)
            prefixes.append(prefix)
            prefix_lengths.append(len(prefix))
        max_prefix_length = max(prefix_lengths) + 1
        return HasLocaleStr(
            "\n".join(
                template.format(
                    localized=indent(localized, " " * max_prefix_length)[
                        len(prefixes[index]) + 1 :
                    ],
                    prefix=self._get_prefix(localizer, index),
                )
                for index, localized in enumerate(localizeds)
            )
        )

    @abstractmethod
    def _get_prefix(self, localizer: Localizer, index: int, /) -> str:
        pass


@final
class OrderedList(_List):
    """
    Represent multiple localizables in an ordered list.
    """

    _PREFIX_TEMPLATE_LEFT_TO_RIGHT = "{index}."
    _PREFIX_TEMPLATE_RIGHT_TO_LEFT = ".{index}"

    @override
    def _get_prefix(self, localizer: Localizer, index: int, /) -> str:
        if localizer.locale.character_order == "right-to-left":
            template = self._PREFIX_TEMPLATE_RIGHT_TO_LEFT
        else:
            template = self._PREFIX_TEMPLATE_LEFT_TO_RIGHT
        return template.format(index=index + 1)


@final
class UnorderedList(_List):
    """
    Represent multiple localizables in an unordered list.
    """

    @override
    def _get_prefix(self, localizer: Localizer, index: int, /) -> str:
        return "-"


class _Enumeration(_LocalizableSequence, Localizable):
    _LOCALIZABLE: ClassVar[Localizable]

    @override
    def localize(self, localizer: Localizer, /) -> HasLocale & str:
        if len(self.localizables) == 0:
            return HasLocaleStr("")
        if len(self.localizables) == 1:
            return self.localizables[0].localize(localizer)
        return self._LOCALIZABLE.format(
            most=", ".join(
                part.localize(localizer) for part in self.localizables[0:-1]
            ),
            last=self.localizables[-1],
        ).localize(localizer)


@final
class AnyEnumeration(_Enumeration):
    """
    An enumeration where any of the localizables may be applicable.
    """

    _LOCALIZABLE = _("{most}, or {last}")


@final
class AllEnumeration(_Enumeration):
    """
    An enumeration where all of the localizables are applicable.
    """

    _LOCALIZABLE = _("{most}, and {last}")


def do_you_mean(*available_options: str) -> Localizable:
    """
    Produce a message listing available options.
    """
    match len(available_options):
        case 0:
            return _("There are no available options.")
        case 1:
            return _("Do you mean {available_option}?").format(
                available_option=available_options[0]
            )
        case _:
            return _("Do you mean one of {available_options}?").format(
                available_options=AnyEnumeration(*sorted(map(str, available_options)))
            )
