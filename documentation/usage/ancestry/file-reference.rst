File reference
==============

A :py:class:`betty.model.ancestry.FileReference` describes the relationship between an entity and a :doc:`File <file>`.

Fields
------
``id`` (``str``)
    The file reference's own entity ID.
``file`` (:doc:`File <file>`)
    The referenced file.
``referee`` (:py:class:`betty.model.ancestry.HasFileReferences`)
    The entity referencing the file.
