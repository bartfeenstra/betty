Place
=====

A :py:class:`betty.ancestry.Place` describes a location or an area in the world, such as a country, town, lake, or building.

Fields
------
Places inherit from:

- :doc:`/usage/ancestry/privacy`

``encloses`` (optional ``Place``)
    Another place this place encloses or contains.
``enclosed_by`` (optional ``Place``)
    Another place this place is enclosed or contained by.
``events`` (iterable of :doc:`Event </usage/ancestry/event>`)
    The events that took place here.
``files`` (iterable of :doc:`File </usage/ancestry/file>`)
    The files attached to this place.
``id`` (``str``)
    The place's own entity ID.
``links`` (iterable of :doc:`Link </usage/ancestry/link>`)
    The external links for this place.
``names`` (iterable of :doc:`PlaceName </usage/ancestry/place-name>`)
    The place's names.
