Name
====

A :py:class:`betty.ancestry.name.Name` describes a name that can be translated, and has
a date to indicate its usage.

Fields
------

``date`` (:doc:`Datey </usage/ancestry/date>`)
    When this name was used.
``id`` (``str``)
    The name's own entity ID.
``locale`` (optional ``str``)
    The name's locale as an `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
``name`` (``str``)
    The human-readable name.
