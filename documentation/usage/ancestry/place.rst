Place
=====

A :py:class:`betty.ancestry.place.Place` describes a location or an area in the world, such as a country, town, lake, or
building.

Fields
------
Places inherit from:

- :doc:`/usage/ancestry/privacy`

``enclosees`` (``Iterable[Place]``)
    Other places this place encloses or contains.
``enclosers`` (``Iterable[Place]``)
    Other places this place is enclosed or contained by.
``events`` (iterable of :doc:`Event </usage/ancestry/event>`)
    The events that took place here.
``files`` (iterable of :doc:`File </usage/ancestry/file>`)
    The files attached to this place.
``id`` (``str``)
    The place's own entity ID.
``links`` (iterable of :doc:`Link </usage/ancestry/link>`)
    The external links for this place.
``names`` (iterable of :doc:`Name </usage/ancestry/name>`)
    The place's names.
