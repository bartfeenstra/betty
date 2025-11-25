Presence role plugins
=====================

Presence roles are used to indicate the **role** a :doc:`/usage/ancestry/person` has in an :doc:`/usage/ancestry/event`,
such as the subject, a witness, or an officiant.

Creating a presence role
------------------------

Create a new class that extends :py:class:`betty.ancestry.presence_role.PresenceRole` and implements the abstract
methods, for example:

.. code-block:: python

   from betty.ancestry.presence_role import PresenceRole, PresenceRolePlugin

   @PresenceRolePlugin(
       id="my-presence-role",
       label=_("My Presence Role"),
   )
   class MyPresenceRole(PresenceRole):
       pass


Tell Betty about your presence role by registering it as an entry point. Given the role above in a module ``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.presence_role']
   'my-module-my-presence-role' = 'my_package.my_module.MyPresenceRole'

See also
--------
Read more about how to use roles and Betty's built-in presence roles at :doc:`/usage/ancestry/presence-role`.
