"""
Wikipedia copyright notices.
"""

from collections.abc import Sequence
from contextlib import suppress
from typing import Self

from typing_extensions import override

from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.copyright_notice import CopyrightNotice
from betty.fetch import FetchError
from betty.locale import negotiate_locale, to_babel_identifier
from betty.locale.localizable import _, Localizable, call
from betty.locale.localizer import Localizer
from betty.plugin import ShorthandPluginBase


class WikipediaContributors(ShorthandPluginBase, AppDependentFactory, CopyrightNotice):
    """
    The copyright for resources on Wikipedia.
    """

    _plugin_id = "wikipedia-contributors"
    _plugin_label = _("Wikipedia contributors")

    def __init__(self, available_locales: Sequence[str] | None = None):
        self._available_locales = available_locales or []

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        available_locales = []
        try:
            languages_response = await app.fetcher.fetch(
                "https://en.wikipedia.org/w/api.php?action=query&titles=Wikipedia:Copyrights&prop=langlinks&lllimit=500&format=json&formatversion=2"
            )
        except FetchError:
            pass
        else:
            for link in languages_response.json["query"]["pages"][0]["langlinks"]:
                with suppress(ValueError):
                    available_locales.append(to_babel_identifier(link["lang"]))
        return cls(available_locales)

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
        return call(self._localize_url)

    def _localize_url(self, localizer: Localizer) -> str:
        locale = negotiate_locale([localizer.locale, "en"], self._available_locales)
        return f"https://{locale}.wikipedia.org/wiki/Wikipedia:Copyrights"
