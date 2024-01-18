Event
=====

An :py:class:`betty.model.ancestry.Event` is something that happened at some time, such as a birth, death, or marriage.

Fields
------
Events inherit from:

- :doc:`privacy`

``date`` (:doc:`Datey <date>`)
    When the event took place.
``event_type`` (:doc:`EventType <event-type>`)
    The event's type.
``files`` (iterable of :doc:`File <file>`)
    The files attached to this event.
``citations`` (iterable of :doc:`Citation <citation>`)
    The citations for this event.
``description`` (optional ``str``)
    The event's human-readable description.
``id`` (``str``)
    The event's own entity ID.
``place`` (:doc:`Place <place>`)
    Where the event took place.
``presences`` (iterable of :doc:`Presence <presence>`)
    :doc:`People's <person>` presences at this event.
