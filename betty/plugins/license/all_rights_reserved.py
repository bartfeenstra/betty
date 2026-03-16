"""
The all rights reserved license.
"""

from typing import final, override

from betty.license import License, LicenseDefinition
from betty.locale.localizable import Localizable
from betty.locale.localizable.gettext import _


@final
@LicenseDefinition("all-rights-reserved", label=_("All rights reserved"))
class AllRightsReserved(License):
    """
    .. plugin:: license:all-rights-reserved.
    """

    @property
    @override
    def summary(self) -> Localizable:
        return self.plugin().label

    @property
    @override
    def text(self) -> Localizable:
        return _(
            "No part may be reproduced or distributed in any form or by any means, without express written permission from the copyright holder, or unless permitted by copyright law."
        )
