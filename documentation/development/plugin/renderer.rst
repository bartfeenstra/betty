Renderer plugins
================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.render.Renderer` ``&`` :py:class:`betty.plugin.Plugin`
   * -  Repository
     -  :py:class:`betty.render.RENDERER_REPOSITORY`

Renderers convert textual content to HTML. A renderer is often built to support one or more related source content types.

Creating a renderer
-------------------

#. Create a new class that extends both :py:class:`betty.render.Renderer` and :py:class:`betty.plugin.Plugin` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.machine_name import MachineName
     from betty.plugin import Plugin
     from betty.render import Renderer

     class MyRenderer(Renderer, Plugin):
       @override
       @classmethod
       def plugin_id(cls) -> MachineName:
           return "my-module-my-renderer"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your renderer by registering it as an entry point. Given the renderer above in a module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.renderer']
          'my-module-my-renderer' = 'my_package.my_module.MyRenderer'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.renderer': [
                      'my-module-my-renderer=my_package.my_module.MyRenderer',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)
