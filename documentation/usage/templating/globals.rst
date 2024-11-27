Globals
=======

Jinja2 `globals <https://jinja.palletsprojects.com/en/3.1.x/templates/#list-of-global-functions>`_ are
often data or functions that do not are not :doc:`filters </usage/templating/filters>` or :doc:`tests </usage/templating/tests>`.

Built-in globals
----------------
In addition to Jinja2's built-in globals, Betty provides the following:

``app`` (:py:class:`betty.app.App`)
    The currently running Betty application.
``citer`` (:py:class:`betty.html.Citer`)
    The ledger of citation references on the current page.
``breadcrumbs`` (:py:class:`betty.html.Breadcrumbs`)
    The ledger of `breadcrumbs <https://en.wikipedia.org/wiki/Breadcrumb_navigation>`_ on the current page.
``entity_contexts`` (:py:class:`betty.jinja2.EntityContexts`)
    The ledger of primary entities in the current template context.
``localizer`` (:py:class:`betty.locale.localizer.Localizer`)
    The localizer for the current template context.
``project`` (:py:class:`betty.project.Project`)
    The project the template is being rendered for.
``public_css_paths`` (a sequence of :py:class:`str`)
    The paths to the public CSS files used for all pages.
``public_js_paths`` (a sequence of :py:class:`str`)
    The paths to the public JS files used for all pages.
``today`` (:py:class:`betty.date.Date`)
    The current date.
