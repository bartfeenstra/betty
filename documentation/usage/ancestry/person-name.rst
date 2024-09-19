Person Name
===========

A :py:class:`betty.ancestry.person_name.PersonName` describes a name for a :doc:`person </usage/ancestry/person>`.

Fields
------
Names inherit from:

- :doc:`/usage/ancestry/privacy`

``affiliation`` (optional ``str``)
    The person's affiliation or family name, their surname, or last name.
``citations`` (iterable of :doc:`Citation </usage/ancestry/citation>`)
    The citations for this person.
``id`` (``str``)
    The name's own entity ID.
``individual`` (optional ``str``)
    The person's individual or personal name, their first name, or given name.
``locale`` (optional ``str``)
    The name's locale as an `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
``person`` (:doc:`Person </usage/ancestry/person>`)
    The person whose name this is.
