Content providers
=================

Content providers inherit from :py:class:`betty.content_provider.ContentProvider`.

Built-in content providers
--------------------------
``box`` (:py:class:`betty.content_provider.content_providers.Box`)
    A box whose dimensions can be configured.
``maps-map`` (:py:class:`betty.project.extension.maps.content_provider.Map`)
    Display an interactive map for the :doc:`places </usage/ancestry/place.rst>` associated with a resource.
``maps-map-attribution`` (:py:class:`betty.project.extension.maps.content_provider.MapAttribution`)
    Display the attribution for a map.
``notes`` (:py:class:`betty.content_provider.content_providers.Notes`)
    Display a resource's :doc:`notes </usage/ancestry/note.rst>`
``raspberry-mint-citations`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Citations`)
    The citations for a document resource that is an entity.
``raspberry-mint-color-style`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.ColorStyle`)
    Change the color style for all containing content.
``raspberry-mint-columns`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Columns`)
    A container with one or more columns.
``raspberry-mint-enclosees`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Enclosees`)
    Show the places enclosed by a place document resource.
``raspberry-mint-entity-card`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.EntityCard`)
    A card featuring an entity.
``raspberry-mint-external-links`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.ExternalLinks`)
    A resource's external links.
``raspberry-mint-facts`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Facts`)
    Other entities that reference a citation or source to back up their claims.
``raspberry-mint-families`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Families`)
    Display a person's families.
``raspberry-mint-file-referees`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.FileReferees`)
    Show the entities referencing a document resource that is a file.
``raspberry-mint-media`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Media`)
    Show a file entity as media.
``raspberry-mint-media-gallery`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.MediaGallery`)
    Show a media gallery of a resource's associated files.
``raspberry-mint-presences`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Presences`)
    People's presences at an event.
``raspberry-mint-section`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Section`)
    Display other content in a section with a heading and a permanent link.
``raspberry-mint-timeline`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Timeline`)
    A timeline of events.
``render`` (:py:class:`betty.content_provider.content_providers.Render`)
    Display rendered content.
``trees-tree`` (:py:class:`betty.project.extension.trees.content_provider.Tree`)
    Display an interactive family tree for the :doc:`places </usage/ancestry/person.rst>` associated with a resource.
``wiki-wikipedia-summary`` (:py:class:`betty.project.extension.wiki.content_provider.WikipediaSummary`)
    Display Wikipedia summaries for the current page resource if it is an entity that can have links.

See also
--------
- :doc:`/development/plugin/content-provider`
