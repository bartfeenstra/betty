File reference
==============

A :py:class:`betty.ancestry.file_reference.FileReference` describes the relationship between an entity and a :doc:`File </usage/ancestry/file>`.

Fields
------
``id`` (``str``)
    The file reference's own entity ID.
``file`` (:doc:`File </usage/ancestry/file>`)
    The referenced file.
``referee`` (:py:class:`betty.ancestry.has_file_references.HasFileReferences`)
    The entity referencing the file.
