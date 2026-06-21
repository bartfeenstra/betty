"""
The public domain license.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.license import License, LicenseDefinition
from betty.localizables.gettext import _

if TYPE_CHECKING:
    from betty.localizable import Localizable


@final
@LicenseDefinition("public-domain", label=_("Public domain"))
class PublicDomain(License):
    """
    .. plugin:: license:public-domain.
    """

    @property
    @override
    def summary(self) -> Localizable:
        return self.plugin().label

    @property
    @override
    def text(self) -> Localizable:
        return _(
            "Works in the public domain can be used or referenced without permission, because nobody holds any exclusive rights over these works (anymore)."
        )
