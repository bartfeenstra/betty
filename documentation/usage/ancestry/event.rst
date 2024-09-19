Event
=====

An :py:class:`betty.ancestry.event.Event` is something that happened at some time, such as a birth, death, or marriage.

Fields
------
Events inherit from:

- :doc:`/usage/ancestry/privacy`

``date`` (:doc:`Datey </usage/ancestry/date>`)
    When the event took place.
``event_type`` (:doc:`EventType </usage/ancestry/event-type>`)
    The event's type.
``files`` (iterable of :doc:`File </usage/ancestry/file>`)
    The files attached to this event.
``citations`` (iterable of :doc:`Citation </usage/ancestry/citation>`)
    The citations for this event.
``description`` (optional :doc:`/usage/ancestry/static-translations`)
    The event's human-readable description.
``id`` (``str``)
    The event's own entity ID.
``place`` (:doc:`Place </usage/ancestry/place>`)
    Where the event took place.
``presences`` (iterable of :doc:`Presence </usage/ancestry/presence>`)
    :doc:`People's </usage/ancestry/person>` presences at this event.
