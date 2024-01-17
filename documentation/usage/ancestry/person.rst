Person
======

A :py:class:`betty.model.ancestry.Person` describes an individual human being.

Fields
------
People inherit from:

- :doc:`privacy`

``children`` (an iterable of ``Person``)
    The person's children.
``files`` (iterable of :doc:`File <file>`)
    The files attached to this person.
``citations`` (iterable of :doc:`Citation <citation>`)
    The citations for this person.
``id`` (``str``)
    The person's own entity ID.
``links`` (iterable of :doc:`Link <link>`)
    The external links for this person.
``names`` (iterable of :doc:`PersonName <person-name>`)
    The person's names.
``parents`` (an iterable of ``Person``)
    The person's parents.
``presences`` (iterable of :doc:`Presence <presence>`)
    The person's presences at :doc:`events <event>`.
``siblings`` (an iterable of ``Person``)
    The person's siblings.
