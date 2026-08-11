"""
Complex/markup localizables.
"""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from textwrap import indent
from typing import TYPE_CHECKING, Any, ClassVar, Final, final, override

from betty.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)
from betty.localizables.gettext import _, pgettext
from betty.localized import LocalizedStr

if TYPE_CHECKING:
    from collections.abc import Sequence

    from betty.localizer import Localizer

join_separator: Final[Localizable] = pgettext("localizable-join-separator", ", ")
join_and: Final[Localizable] = pgettext("localizable-join-and", "{first} and {second}")
join_and_many: Final[Localizable] = pgettext(
    "localizable-join-and-many", "{most}, and {last}"
)
join_or: Final[Localizable] = pgettext("localizable-join-or", "{first} or {second}")
join_or_many: Final[Localizable] = pgettext(
    "localizable-join-or-many", "{most}, or {last}"
)


class LocalizableSequence(metaclass=ABCMeta):
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
    __slots__ = ("_localizables",)

    def __init__(self, *localizables: ResolvableLocalizable):
        self._localizables = tuple(map(resolve_localizable, localizables))

    @override
    @property
    def localizables(self) -> Sequence[Localizable]:
        return self._localizables


class _Join(_LocalizableSequence, Localizable):
    _separator: ClassVar[str]

    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        return LocalizedStr(
            self._separator.join(
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

    _separator: ClassVar[str] = ""


@final
class Paragraph(_Join):
    """
    Represent multiple localizables as a single paragraph of text.
    """

    _separator: ClassVar[str] = " "


@final
class Lines(_Join):
    """
    Represent multiple localizables as multiple lines of text.
    """

    _separator: ClassVar[str] = "\n"


@final
class Paragraphs(_Join):
    """
    Represent multiple localizables as multiple paragraphs of text.
    """

    _separator: ClassVar[str] = "\n\n"


class _List(_LocalizableSequence, Localizable):
    _template_left_to_right: Final[str] = "{prefix} {localized}"
    _template_right_to_left: Final[str] = "{localized} {prefix}"

    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        if not self.localizables:
            return LocalizedStr("")
        localizeds = []
        prefixes = []
        prefix_lengths = []
        if localizer.locale.character_order == "right-to-left":
            template = self._template_right_to_left
        else:
            template = self._template_left_to_right
        for index, localizable in enumerate(self._localizables):
            localizeds.append(localizable.localize(localizer))
            prefix = self._get_prefix(localizer, index)
            prefixes.append(prefix)
            prefix_lengths.append(len(prefix))
        max_prefix_length = max(prefix_lengths) + 1
        return LocalizedStr(
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

    _prefix_template_left_to_right: Final[str] = "{index}."
    _prefix_template_right_to_left: Final[str] = ".{index}"

    @override
    def _get_prefix(self, localizer: Localizer, index: int, /) -> str:
        if localizer.locale.character_order == "right-to-left":
            template = self._prefix_template_right_to_left
        else:
            template = self._prefix_template_left_to_right
        return template.format(index=index + 1)


@final
class UnorderedList(_List):
    """
    Represent multiple localizables in an unordered list.
    """

    @override
    def _get_prefix(self, localizer: Localizer, index: int, /) -> str:
        return "-"


class _NaturalJoin(_LocalizableSequence, Localizable):
    _join: ClassVar[Localizable]
    _join_many: ClassVar[Localizable]

    @final
    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        match len(self.localizables):
            case 0:
                return LocalizedStr("")
            case 1:
                return self.localizables[0].localize(localizer)
            case 2:
                return self._join.format(
                    first=self._localizables[0], second=self._localizables[1]
                ).localize(localizer)
        return self._join_many.format(
            most=join_separator.localize(localizer).join(
                part.localize(localizer) for part in self.localizables[0:-1]
            ),
            last=self.localizables[-1],
        ).localize(localizer)


@final
class JoinAnd(_NaturalJoin):
    """
    An enumeration where all of the localizables are applicable.
    """

    _join: ClassVar[Localizable] = join_and
    _join_many: ClassVar[Localizable] = join_and_many


@final
class JoinOr(_NaturalJoin):
    """
    An enumeration where any of the localizables may be applicable.
    """

    _join: ClassVar[Localizable] = join_or
    _join_many: ClassVar[Localizable] = join_or_many


class _Template(Localizable):
    __slots__ = ("_text",)
    _template: ClassVar[Localizable]

    @final
    def __init__(self, text: ResolvableLocalizable, /):
        self._text = text

    @final
    @override
    def localize(self, localizer: Localizer, /) -> LocalizedStr:
        return self._template.format(text=self._text).localize(localizer)


@final
class Quote(_Template):
    """
    Format text as a literal quote.
    """

    _template: ClassVar[Localizable] = pgettext("localizable-quote", '"{text}"')


def do_you_mean(*available_options: Any) -> Localizable:
    """
    Produce a message listing available options.
    """
    if available_options:
        return _("Do you mean {available_options}?").format(
            available_options=JoinOr(*sorted(map(str, available_options)))
        )
    return _("There are no available options.")
