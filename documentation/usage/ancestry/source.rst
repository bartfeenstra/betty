Source
======

:py:class:`betty.model.ancestry.Source` entities describe where the information in an ancestry comes from,
such as archives, correspondence, or personal accounts.

Fields
------
Sources inherit from:

- :doc:`privacy`

``author`` (``str``)
    The human-readable name of the source's author.
``citations`` (iterable of :doc:`Citation <citation>`)
    The citations referencing the source.
``contained_by`` (optional ``Source``)
    Another source that contains this one.
``contains`` (iterable of ``Source``)
    Other sources contained by this one.
``date`` (:doc:`Datey <date>`)
    The source (access) date.
``files`` (iterable of :doc:`File <file>`)
    The files attached to this source.
``id`` (``str``)
    The source's own entity ID.
``links`` (iterable of :doc:`Link <link>`)
    The external links for this source.
``name`` (``str``)
    The human-readable name.
``publisher`` (``str``)
    The human-readable name of the source's publisher.
