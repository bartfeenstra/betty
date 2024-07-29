Enclosure
=========

An :py:class:`betty.model.ancestry.Enclosure` acts as a bridge that links :doc:`places </usage/ancestry/place>` together that
enclose, or contain each other.

Fields
------
``citations`` (iterable of :doc:`Citation </usage/ancestry/citation>`)
    The citations for this enclosure.
``date`` (:doc:`Datey </usage/ancestry/date>`)
    When these places enclosed each other.
``encloses`` (:doc:`Place </usage/ancestry/place>`)
    The place that is enclosed by the ``enclosed_by``.
``enclosed_by`` (:doc:`Place </usage/ancestry/place>`)
    The place that encloses ``encloses``.
``id`` (``str``)
    The enclosure's own entity ID.
