"""
Copyright notices for the Betty demonstration site.
"""

from typing import final

from typing_extensions import override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.locale.localizable import Localizable
from betty.locale.localizable.plain import Plain


@final
@CopyrightNoticeDefinition("streetmix", label=Plain("Streetmix LLC"))
class Streetmix(CopyrightNotice):
    """
    The copyright for Streetmix resources.
    """

    @override
    @property
    def summary(self) -> Localizable:
        return self.plugin().label

    @override
    @property
    def text(self) -> Localizable:
        return self.plugin().label

    @override
    @property
    def url(self) -> Localizable:
        return Plain("https://github.com/streetmix/streetmix")
