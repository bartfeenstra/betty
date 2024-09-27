Enclosure
=========

An :py:class:`betty.ancestry.enclosure.Enclosure` acts as a bridge that links :doc:`places </usage/ancestry/place>`
together that enclose, or contain each other.

Fields
------
``citations`` (iterable of :doc:`Citation </usage/ancestry/citation>`)
    The citations for this enclosure.
``date`` (:doc:`Datey </usage/ancestry/date>`)
    When these places enclosed each other.
``enclosee`` (:doc:`Place </usage/ancestry/place>`)
    The place that is enclosed by ``encloser``.
``encloser`` (:doc:`Place </usage/ancestry/place>`)
    The place that encloses ``enclosee``.
``id`` (``str``)
    The enclosure's own entity ID.
