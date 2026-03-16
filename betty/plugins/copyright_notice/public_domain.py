"""
The public domain copyright notice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.locale.localizable.gettext import _

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable


@final
@CopyrightNoticeDefinition("public-domain", label=_("Public domain"))
class PublicDomain(CopyrightNotice):
    """
    .. plugin:: copyright-notice:public-domain.
    """

    @property
    @override
    def summary(self) -> Localizable:
        return _("Public domain")

    @property
    @override
    def text(self) -> Localizable:
        return _(
            "Works in the public domain can be used or referenced without permission, because nobody holds any exclusive rights over these works (anymore)."
        )
