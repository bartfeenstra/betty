Console command plugins
===================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.console.command.Command`
   * -  Repository
     -  :py:class:`betty.console.command.COMMAND_REPOSITORY`

Betty's :doc:`console </usage/console>` allows you to run Betty by invoking commands. These commands
are built using :py:mod:`argparse`.

Creating a command
------------------

#. Create a new class that extends :py:class:`betty.console.command.Command` and implements the abstract methods,
   for example:

   .. code-block:: python

    from typing import override
    from betty.console.commands import Command
    from betty.machine_name import MachineName

    class MyCommand(Command):
        @override
        @classmethod
        def plugin_id(cls) -> MachineName:
            return "my-module-my-command"

        # Implement remaining abstract methods...
        ...


#. Tell Betty about your command by registering it as an entry point. Given the command above in a module ``my_package.my_module``, add the following to your Python package:

   .. code-block:: toml

       [project.entry-points.'betty.command']
       'my-module-my-command' = 'my_package.my_module.MyCommand'
              
#. Configure the argument parser and return the function to invoke the command:

   .. code-block:: python

     import argparse
     from typing import override
     from betty.console.commands import Command, command
     from betty.machine_name import MachineName

     class MyCommand(Command):
         @override
         async def configure(
             self, parser: argparse.ArgumentParser
         ) -> Callable[..., Awaitable[None]]:
             return self._invoke

         async def _invoke(self) -> None:
             # Perform the actual command...

   Arguments can be added through the parser, and are passed on to the command function as keyword arguments:

   .. code-block:: python

     import argparse
     from typing import override
     from betty.console import add_project_argument
     from betty.console.commands import Command, command
     from betty.machine_name import MachineName
     from betty.project import Project

     class MyCommand(Command):
         @override
         async def configure(
             self, parser: argparse.ArgumentParser
         ) -> Callable[..., Awaitable[None]]:
             # Require a project by adding a project configuration file argument:
             await add_project_argument(parser, self._app)
             # Add another, custom argument:
             parser.add_argument("--my-first-argument")
             return self._invoke

         async def _invoke(self, project: Project, my_first_argument: str) -> None:
             # Perform the actual command...


See also
--------
Read more about how to use the console and Betty's built-in commands at :doc:`/usage/console`.

