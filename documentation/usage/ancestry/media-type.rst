Media Type
==========

A :py:class:`betty.media_type.MediaType` describes a file's `media type <https://en.wikipedia.org/wiki/Media_type>`_,
such as whether it is a JPG image, or a PDF document.

Fields
------
``type`` (``str``)
    For example: ``text`` if the media type is ``text/plain``.
``subtype`` (``str``)
    For example: ``ls`` if the media type is ``application/ld+json``.
``subtypes`` (iterable of ``str``)
    For example: ``['vnd', 'oasis', 'opendocument', 'text']`` if the media type is ``application/vnd.oasis.opendocument.text``.
``suffix`` (``str``)
    For example: ``json`` if the media type is ``application/ld+json``.
``parameters`` (iterable of ``str``)
    For example: ``['charset=UTF-8']`` if the media type is ``text/html; charset=UTF-8``.
