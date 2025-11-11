Console command plugins
=======================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.console.command.Command`
   * -  Repository
     -  :py:class:`betty.app.App.command_repository`

Betty's :doc:`console </usage/console>` allows you to run Betty by invoking commands. These commands
are built using :py:mod:`argparse`.

Creating a command
------------------

Create a new class decorated with :py:class:`betty.console.command.CommandDefinition`, and that implements the
abstract methods, for example:

.. code-block:: python

   import argparse
   from typing import override

   from betty.console.command import Command, CommandDefinition, CommandFunction

   @CommandDefinition(
       id="my-command",
       label=_("My Command"),
   )
   class MyCommand(Command):
       @override
       async def configure(
           self, parser: argparse.ArgumentParser
       ) -> CommandFunction:
           ... # Implement this method...

Tell Betty about your command by registering it as an entry point. Given the command above in a module
``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.command']
   'my-command' = 'my_package.my_module.MyCommand'
              
Examples
^^^^^^^^

Arguments can be added through the parser, and are passed on to the command function as keyword arguments:

.. code-block:: python

   import argparse
   from typing import override

   from betty.console import add_project_argument
   from betty.console.command import Command, CommandFunction
   from betty.project import Project

   class MyCommand(Command):
       @override
       async def configure(
           self, parser: argparse.ArgumentParser
       ) -> CommandFunction:
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

