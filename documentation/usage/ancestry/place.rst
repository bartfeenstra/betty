Place
=====

A :py:class:`betty.model.ancestry.Places` describes a location or an area in the world, such as a country, town, lake, or building.

Fields
------
Places inherit from:

- :doc:`privacy`

``encloses`` (optional ``Place``)
    Another place this place encloses or contains.
``enclosed_by`` (optional ``Place``)
    Another place this place is enclosed or contained by.
``events`` (iterable of :doc:`Event <event>`)
    The events that took place here.
``files`` (iterable of :doc:`File <file>`)
    The files attached to this place.
``id`` (``str``)
    The place's own entity ID.
``links`` (iterable of :doc:`Link <link>`)
    The external links for this place.
``names`` (iterable of :doc:`PlaceName <place-name>`)
    The place's names.
