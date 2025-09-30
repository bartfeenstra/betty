"""
Copyright notices for the Betty demonstration site.
"""

from typing import final

from typing_extensions import override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.locale.localizable import Localizable, StaticTranslations


@final
@CopyrightNoticeDefinition(
    id="streetmix",
    label=StaticTranslations("Streetmix LLC"),
)
class Streetmix(CopyrightNotice):
    """
    The copyright for Streetmix resources.
    """

    @override
    @property
    def summary(self) -> Localizable:
        return self.plugin.label

    @override
    @property
    def text(self) -> Localizable:
        return self.plugin.label

    @override
    @property
    def url(self) -> Localizable:
        return StaticTranslations("https://github.com/streetmix/streetmix")
