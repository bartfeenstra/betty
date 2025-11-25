Event type plugins
==================

Event types are used to indicate the **type** of an :doc:`/usage/ancestry/event`, such as a birth, a death, or an marriage.

Creating an event type
----------------------

Create a new class that extends :py:class:`betty.ancestry.event_type.EventType` and implements the abstract methods, for
example:

.. code-block:: python

   from betty.ancestry.event_type import EventType, EventTypePlugin

   @EventTypePlugin(
       id="my-event-type",
       label=_("My Event Type"),
   )
   class MyEventType(EventType):
       pass


Tell Betty about your event type by registering it as an entry point. Given the event type above in a module
``my_package.my_module``, add the following to your Python package:

.. code-block:: toml

   [project.entry-points.'betty.event_type']
   'my-event-type' = 'my_package.my_module.MyEventType'

See also
--------
Read more about how to use event types and Betty's built-in event types at :doc:`/usage/ancestry/event-type`.
