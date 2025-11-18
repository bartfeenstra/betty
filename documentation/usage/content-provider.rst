Content providers
=================

Content providers inherit from :py:class:`betty.content_provider.ContentProvider`.

Built-in content providers
--------------------------
``maps-map`` (:py:class:`betty.project.extension.maps.content_provider.Map`)
    Display an interactive map for the :doc:`places </usage/ancestry/place.rst>` associated with a resource.
``notes`` (:py:class:`betty.content_provider.content_providers.Notes`)
    Display a resource's :doc:`notes </usage/ancestry/note.rst>`
``plain-text`` (:py:class:`betty.content_provider.content_providers.PlainText`)
    Display plain text.
``raspberry-mint-family`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Family`)
    Display a person's families.
``raspberry-mint-featured-entities`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.FeaturedEntities`)
    Display one or more entities in cards.
``raspberry-mint-media`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Media`)
    Show a media gallery of a resource's associated files.
``raspberry-mint-section`` (:py:class:`betty.project.extension.raspberry_mint.content_provider.Section`)
    Display other content in a section with a heading and a permanent link.
``trees-tree`` (:py:class:`betty.project.extension.trees.content_provider.Tree`)
    Display an interactive family tree for the :doc:`places </usage/ancestry/person.rst>` associated with a resource.
``wiki-wikipedia-summary`` (:py:class:`betty.project.extension.wiki.content_provider.WikipediaSummary`)
    Display Wikipedia summaries for the current page resource if it is an entity that can have links.

See also
--------
- :doc:`/development/plugin/content-provider`
