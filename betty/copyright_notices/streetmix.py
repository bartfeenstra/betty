"""
The Streetmix copyright notice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.localizables.plain import Plain

if TYPE_CHECKING:
    from betty.localizable import Localizable


@final
@CopyrightNoticeDefinition("streetmix", label=Plain("Streetmix LLC"))
class Streetmix(CopyrightNotice):
    """
    .. plugin:: copyright-notice:streetmix.
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
