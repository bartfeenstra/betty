CLI command plugins
===================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.cli.commands.Command`
   * -  Repository
     -  :py:class:`betty.cli.commands.COMMAND_REPOSITORY`

Betty's :doc:`Command Line Interface </usage/cli>` allows you to run Betty by invoking commands. These commands
are built using `Click <https://click.palletsprojects.com/>`_.

Creating a command
------------------

#. Create a new asynchronous function, decorated with :py:func:`betty.cli.commands.command` and :py:func:`click.command`,
   for example:

   .. code-block:: python

     import click
     from betty.cli.commands import command

     @click.command()
     @command
     async def my_command() -> None:
       # Do what your command needs to do here...
       ...


#. Tell Betty about your command by registering it as an entry point. Given the command above in a module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.command']
          'my-command' = 'my_package.my_module.my_command'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.command': [
                      'my-command=my_package.my_module.my_command',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)

Accessing the project
^^^^^^^^^^^^^^^^^^^^^

To make your command use a specific Betty project, use the :py:func:`betty.cli.commands.pass_project` decorator:

.. code-block:: python

 import click
 from betty.project import Project
 from betty.cli.commands import command, pass_project

 @click.command()
 @pass_project
 @command
 async def my_command(project: Project) -> None:
   # Do what your command needs to do here...
   ...

This also gives you access to the Betty application through :py:attr:`betty.project.Project.app`.

Accessing the project
^^^^^^^^^^^^^^^^^^^^^

If your command does not need a project, but does require the Betty application, use the
:py:func:`betty.cli.commands.pass_app` decorator:

.. code-block:: python

 import click
 from betty.app import App
 from betty.cli.commands import command, pass_app

 @click.command()
 @pass_app
 @command
 async def my_command(app: App) -> None:
   # Do what your command needs to do here...
   ...

See also
--------
Read more about how to use the Command Line Interface and Betty's built-in commands at :doc:`/usage/cli`.

