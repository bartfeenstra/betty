File
====

A :py:class:`betty.model.ancestry.File` describes a file, such as an image or a PDF document, that is attached to other entities.

Fields
------
Files inherit from:

- :doc:`privacy`

``citations`` (iterable of :doc:`Citation <citation>`)
    The citations for this file.
``description`` (optional ``str``)
    The file's human-readable description.
``entities`` (iterable of any entity)
    The entities this file is attached to.
``id`` (``str``)
    The file's own entity ID.
``links`` (iterable of :doc:`Link <link>`)
    The external links for this file.
``notes`` (iterable of :doc:`Note <note>`)
    The notes for this file.
``media_type`` (:doc:`MediaType <media-type>`)
    The media type of this file.
