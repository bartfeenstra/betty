Source
======

:py:class:`betty.ancestry.source.Source` entities describe where the information in an ancestry comes from,
such as archives, correspondence, or personal accounts.

Fields
------
Sources inherit from:

- :doc:`/usage/ancestry/privacy`

``author`` (optional :doc:`/usage/ancestry/static-translations`)
    The human-readable author of the source.
``citations`` (iterable of :doc:`Citation </usage/ancestry/citation>`)
    The citations referencing the source.
``contained_by`` (optional ``Source``)
    Another source that contains this one.
``contains`` (iterable of ``Source``)
    Other sources contained by this one.
``date`` (:doc:`Datey </usage/ancestry/date>`)
    The source (access) date.
``files`` (iterable of :doc:`File </usage/ancestry/file>`)
    The files attached to this source.
``id`` (``str``)
    The source's own entity ID.
``links`` (iterable of :doc:`Link </usage/ancestry/link>`)
    The external links for this source.
``name`` (optional :doc:`/usage/ancestry/static-translations`)
    The human-readable source name.
``publisher`` (optional :doc:`/usage/ancestry/static-translations`)
    The human-readable publisher of the source.
