Person
======

A :py:class:`betty.ancestry.person.Person` describes an individual human being.

Fields
------
People inherit from:

- :doc:`/usage/ancestry/privacy`

``children`` (an iterable of ``Person``)
    The person's children.
``files`` (iterable of :doc:`File </usage/ancestry/file>`)
    The files attached to this person.
``citations`` (iterable of :doc:`Citation </usage/ancestry/citation>`)
    The citations for this person.
``id`` (``str``)
    The person's own entity ID.
``links`` (iterable of :doc:`Link </usage/ancestry/link>`)
    The external links for this person.
``names`` (iterable of :doc:`PersonName </usage/ancestry/person-name>`)
    The person's names.
``parents`` (an iterable of ``Person``)
    The person's parents.
``presences`` (iterable of :doc:`Presence </usage/ancestry/presence>`)
    The person's presences at :doc:`events </usage/ancestry/event>`.
``siblings`` (an iterable of ``Person``)
    The person's siblings.
