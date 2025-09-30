Renderer plugins
================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.render.Renderer`
   * -  Repository
     -  :py:class:`betty.render.RENDERER_REPOSITORY`

Renderers convert textual content to HTML. A renderer is often built to support one or more related source content
types.

Creating a renderer
-------------------

Create a new class that extends :py:class:`betty.render.Renderer` and implements the abstract methods, for example:

.. code-block:: python

   from betty.render import Renderer, RendererDefinition

   @RendererDefinition(
       id="my-renderer",
       label=_("My Renderer"),
   )
   class MyRenderer(Renderer):
       # Implement remaining abstract methods...
       ...


Tell Betty about your renderer by registering it as an entry point. Given the renderer above in a module
``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.renderer']
   'my-module-my-renderer' = 'my_package.my_module.MyRenderer'
