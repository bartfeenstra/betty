Event dispatching
=================

Betty communicates with its components through an approach called *event dispatching*.
Calling code that wants to let other components know something has happened, will tell
the **event dispatcher** to dispatch an **event**. For each event type, **handlers** may be
registered to be notified whenever an event of that type is dispatched.

At the moment, only :doc:`extensions </development/plugin/extension>` can register event
handlers.

Built-in event types
--------------------
- :py:class:`betty.project.load.LoadAncestryEvent`
- :py:class:`betty.project.load.PostLoadAncestryEvent`
- :py:class:`betty.project.generate.GenerateSiteEvent`
