Presence
========

A :py:class:`betty.ancestry.presence.Presence` acts as a bridge that links a :doc:`/usage/ancestry/person` to an
:doc:`/usage/ancestry/event`.

Fields
------
Presences inherit from:

- :doc:`/usage/ancestry/privacy`

``person`` (:doc:`Person </usage/ancestry/person>`)
    The person who was present at ``event``.
``event`` (:doc:`Event </usage/ancestry/event>`)
    The event ``person`` was present at.
``id`` (``str``)
    The presence's own entity ID.
``role`` (:doc:`PresenceRole </usage/ancestry/presence-role>`)
    ``person``'s role in the event.
