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

#. Create a new class that extends :py:class:`betty.cli.commands.Command` and implements the abstract methods,
   for example:

   .. code-block:: python

    from typing import override
    from betty.cli.commands import Command
    from betty.machine_name import MachineName

    class MyCommand(Command):
      @override
      @classmethod
      def plugin_id(cls) -> MachineName:
          return "my-module-my-command"

      # Implement remaining abstract methods...
      ...


#. Tell Betty about your command by registering it as an entry point. Given the command above in a module 
   ``my_package.my_module``, add the following to your Python package:

   .. tab-set::

      .. tab-item:: pyproject.toml

         .. code-block:: toml

             [project.entry-points.'betty.command']
             'my-module-my-command' = 'my_package.my_module.MyCommand'

      .. tab-item:: setup.py

         .. code-block:: python

             SETUP = {
                 'entry_points': {
                     'betty.command': [
                         'my-module-my-command=my_package.my_module.MyCommand',
                     ],
                 },
             }
             if __name__ == '__main__':
                 setup(**SETUP)
              
#. Build the Click command, decorated with :py:func:`betty.cli.commands.command` (which works almost identically to
   :py:func:`asyncclick.command`), by returning it from your :py:meth:`betty.cli.commands.Command.click_command`
   implementation:

   .. code-block:: python

     from typing import override
     import click
     from betty.cli.commands import Command, command
     from betty.machine_name import MachineName

     class MyCommand(Command):
       @override
       async def click_command(self) -> click.Command:
           @command
           def my_command() -> Any:
             # Implement your Click command.
             ...
           return my_command

       # Implement remaining abstract methods...
       ...

   Building your Click command in your Command plugin allows you to access to all of Betty's ``async`` functionality.


Project-specific commands
^^^^^^^^^^^^^^^^^^^^^^^^^

To make your command use a specific Betty project, use the :py:func:`betty.cli.commands.project_option` decorator:

.. code-block:: python

 from betty.project import Project
 from betty.cli.commands import command, project_option

 @command
 @project_option
 async def my_command(project: Project) -> None:
   # Do what your command needs to do here...
   ...

This also gives you access to the Betty application through :py:attr:`betty.project.Project.app`.

Accessing the application
^^^^^^^^^^^^^^^^^^^^^^^^^

Access the currently running :py:class:`betty.app.App` anywhere in your ``Command`` plugin via ``self._app``.

See also
--------
Read more about how to use the Command Line Interface and Betty's built-in commands at :doc:`/usage/cli`.

