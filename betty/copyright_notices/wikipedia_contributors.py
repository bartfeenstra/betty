"""
The Wikipedia contributors copyright notice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, final, override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.localizable import Localizable


def _copyright_url(language: str, page: str) -> str:
    return f"https://{language}.wikipedia.org/wiki/{page}"


# @todo Wrap this in discovery
@final
@CopyrightNoticeDefinition("wikipedia-contributors", label=_("Wikipedia contributors"))
class WikipediaContributors(CopyrightNotice):
    _url: ClassVar[Localizable] = NotImplementedError

    @override
    @property
    def summary(self) -> Localizable:
        return _("Copyright Wikipedia contributors")

    @override
    @property
    def text(self) -> Localizable:
        return _(
            "Copyright of these works lies with the original authors who contributed them to Wikipedia."
        )

    @override
    @property
    def url(self) -> Localizable:
        return self._url
