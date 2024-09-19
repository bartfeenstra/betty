File
====

A :py:class:`betty.ancestry.file.File` describes a file, such as an image or a PDF document, that is attached to other
entities.

Fields
------
Files inherit from:

- :doc:`/usage/ancestry/privacy`

``citations`` (iterable of :doc:`Citation </usage/ancestry/citation>`)
    The citations for this file.
``description`` (optional :doc:`/usage/ancestry/static-translations`)
    The event's human-readable description.
``entities`` (iterable of any entity)
    The entities this file is attached to.
``id`` (``str``)
    The file's own entity ID.
``links`` (iterable of :doc:`Link </usage/ancestry/link>`)
    The external links for this file.
``notes`` (iterable of :doc:`Note </usage/ancestry/note>`)
    The notes for this file.
``media_type`` (:doc:`MediaType </usage/ancestry/media-type>`)
    The media type of this file.
