Citation
========

:py:class:`betty.ancestry.citation.Citation` entities link 'facts' with :doc:`sources </usage/ancestry/source>`.

Fields
------
Citations inherit from:

- :doc:`/usage/ancestry/privacy`

``date`` (:doc:`Datey </usage/ancestry/date>`)
    The citation (access) date.
``facts`` (iterable of any entity)
    The entities this citation bridges to ``source``.
``files`` (iterable of :doc:`File </usage/ancestry/file>`)
    The files attached to this citation.
``id`` (``str``)
    The citation's own entity ID.
``location`` (``str``)
    A description of which part of ``source`` this citation references.
``source`` (:doc:`Source </usage/ancestry/source>`)
    The source the ``facts`` are bridged to.
