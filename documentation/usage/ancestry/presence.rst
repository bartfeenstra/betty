Presence
========

A :py:class:`betty.model.ancestry.Presence` acts as a bridge that links a :doc:`person` to an :doc:`event`.

Fields
------
Presences inherit from:

- :doc:`privacy`

``person`` (:doc:`Person <person>`)
    The person who was present at ``event``.
``event`` (:doc:`Event <event>`)
    The event ``person`` was present at.
``id`` (``str``)
    The presence's own entity ID.
``role`` (:doc:`PresenceRole <presence-role>`)
    ``person``'s role in the event.
