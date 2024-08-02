Link
====

A :py:class:`betty.model.ancestry.Link` adds external links to entities.

Fields
------
Notes inherit from:

- :doc:`/usage/ancestry/privacy`

``description`` (optional :doc:`/usage/ancestry/static-translations`)
    The event's human-readable description.
``locale`` (optional ``str``)
    The locale of the referenced resource as an `IETF BCP 47 <https://tools.ietf.org/html/bcp47>`_ language tag.
``label`` (optional ``str``)
    The human-readable label of this link, e.g. the link text.
``media_type`` (:doc:`MediaType </usage/ancestry/media-type>`)
    The media type of the referenced resource.
``relationship`` (optional ``str``)
    The `relationship <https://en.wikipedia.org/wiki/Link_relation>`_ between this resource this link is set on and the link target.
``url`` (``url``)
    The URL to the referenced resource.
