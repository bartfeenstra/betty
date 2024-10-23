Presence role plugins
=====================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.ancestry.presence_role.PresenceRole`
   * -  Repository
     -  :py:attr:`betty.project.Project.presence_role_repository`

Presence roles are used to indicate the **role** a :doc:`/usage/ancestry/person` has in an :doc:`/usage/ancestry/event`,
such as the subject, a witness, or an officiant.

Creating a presence role
------------------------

#. Create a new class that extends :py:class:`betty.ancestry.presence_role.PresenceRole` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.ancestry.presence_role import PresenceRole
     from betty.machine_name import MachineName

     class MyPresenceRole(PresenceRole):
       @override
       @classmethod
       def plugin_id(cls) -> MachineName:
           return "my-module-my-presence-role"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your presence role by registering it as an entry point. Given the role above in a module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.presence_role']
          'my-module-my-presence-role' = 'my_package.my_module.MyPresenceRole'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.presence_role': [
                      'my-module-my-presence-role=my_package.my_module.MyPresenceRole',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)

See also
--------
Read more about how to use roles and Betty's built-in presence roles at :doc:`/usage/ancestry/presence-role`.
