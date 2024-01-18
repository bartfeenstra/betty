Citation
========

:py:class:`betty.model.ancestry.Citation` entities link 'facts' with :doc:`sources <source>`.

Fields
------
Citations inherit from:

- :doc:`privacy`

``date`` (:doc:`Datey <date>`)
    The citation (access) date.
``facts`` (iterable of any entity)
    The entities this citation bridges to ``source``.
``files`` (iterable of :doc:`File <file>`)
    The files attached to this citation.
``id`` (``str``)
    The citation's own entity ID.
``location`` (``str``)
    A description of which part of ``source`` this citation references.
``source`` (:doc:`Source <source>`)
    The source the ``facts`` are bridged to.
