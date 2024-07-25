Event type plugins
==================

.. list-table::
   :align: left
   :stub-columns: 1

   * -  Type
     -  :py:class:`betty.model.event_type.EventType`
   * -  Repository
     -  :py:class:`betty.model.event_type.EVENT_TYPE_REPOSITORY`

Event types are used to indicate the **type** of an :doc:`/usage/ancestry/event`, such as a birth, a death, or an marriage.

Creating an event type
----------------------

#. Create a new class that extends :py:class:`betty.model.event_type.EventType` and implements the abstract methods,
   for example:

   .. code-block:: python

     from typing import override
     from betty.model.event_type import EventType

     class MyEventType(EventType):
       @override
       @classmethod
       def plugin_id(cls) -> str:
           return "my-module-my-event-type"

       # Implement remaining abstract methods...
       ...


#. Tell Betty about your event type by registering it as an entry point. Given the event type above in a module ``my_package.my_module``, add the following to your Python package:

.. tab-set::

   .. tab-item:: pyproject.toml

      .. code-block:: toml

          [project.entry-points.'betty.event_type']
          'my-module-my-event-type' = 'my_package.my_module.MyEventType'

   .. tab-item:: setup.py

      .. code-block:: python

          SETUP = {
              'entry_points': {
                  'betty.event_type': [
                      'my-module-my-event-type=my_package.my_module.MyEventType',
                  ],
              },
          }
          if __name__ == '__main__':
              setup(**SETUP)

See also
--------
Read more about how to use event types and Betty's built-in event types at :doc:`/usage/ancestry/event-type`.
