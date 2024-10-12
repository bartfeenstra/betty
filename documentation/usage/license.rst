Licenses
========

Licenses inherit from :py:class:`betty.license.License`.

Built-in licenses
-----------------
:py:class:`betty.license.licenses.AllRightsReserved`
    A license that does not permit the public any rights.
:py:class:`betty.license.licenses.PublicDomain`
    A work is in the `public domain <https://en.wikipedia.org/wiki/Public_domain>`.

Additionally, all licenses from the `SPDX License List <https://spdx.org/licenses/>`_ are available. SPDX licenses IDs
map to Betty license IDs by:

- prefixing them with ``spdx-``
- making them lower case
- replacing anything that is not a letter, digit, or hyphen (``-``) with double hyphens (``--``)

Thus, the ``GPL-3.0+`` SPDX license ID becomes the ``spdx-gpl-3--0--`` Betty license plugin ID.

See also
--------
- :doc:`/development/plugin/license`
