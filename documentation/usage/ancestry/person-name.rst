Person Name
===========

A :py:class:`betty.model.ancestry.PersonName` describes a name for a :doc:`person <person>`.

Fields
------
Names inherit from:

- :doc:`privacy`

``affiliation`` (optional ``str``)
    The person's affiliation or family name, their surname, or last name.
``citations`` (iterable of :doc:`Citation <citation>`)
    The citations for this person.
``id`` (``str``)
    The name's own entity ID.
``individual`` (optional ``str``)
    The person's individual or personal name, their first name, or given name.
``locale`` (optional ``str``)
    The name's locale as an `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
``person`` (:doc:`Person <person>`)
    The person whose name this is.
