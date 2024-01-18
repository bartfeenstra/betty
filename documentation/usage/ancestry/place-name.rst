Place Name
==========

A :py:class:`betty.model.ancestry.PlaceName` describes a name for a :doc:`place <place>`.

Fields
------
Names inherit from:

- :doc:`privacy`

``date`` (:doc:`Datey <date>`)
    When this name was used.
``id`` (``str``)
    The name's own entity ID.
``locale`` (optional ``str``)
    The name's locale as an `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
``name`` (``str``)
    The human-readable name.
``place`` (:doc:`Place <place>`)
    The place whose name this is.
