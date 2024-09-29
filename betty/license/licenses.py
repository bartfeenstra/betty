"""
Provide :py:class:`betty.license.License` plugins.
"""

from typing_extensions import override

from betty.license import License
from betty.locale.localizable import _, Localizable
from betty.plugin import ShorthandPluginBase


class AllRightsReserved(ShorthandPluginBase, License):
    """
    A license that does not permit the public any rights.
    """

    _plugin_id = "all-rights-reserved"
    _plugin_label = _("All rights reserved")

    @property
    @override
    def summary(self) -> Localizable:
        return self._plugin_label

    @property
    @override
    def text(self) -> Localizable:
        return _(
            "No part may be reproduced or distributed in any form or by any means, without express written permission from the copyright holder, or unless permitted by copyright law."
        )


class PublicDomain(ShorthandPluginBase, License):
    """
    A work is in the `public domain <https://en.wikipedia.org/wiki/Public_domain>`.
    """

    _plugin_id = "public-domain"
    _plugin_label = _("Public domain")

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
