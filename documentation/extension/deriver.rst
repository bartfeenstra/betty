The deriver extension
=====================

The *deriver* derives, or infers, events for people based on their existing events. For example, we know that someone's
final disposition, such as a burial or cremation, comes after their death. If a person has a *burial* event without a
date, and a *death* event with a date of *January 1, 1970*, the *deriver* will update the *burial* event with the date
range *sometime after January 1, 1970*.

The *deriver* works for every event type that declares it can be derived, and depending on which other event
types it declares it comes before or after. This means that the behavior of this extension is complex, and dependent on
the event types used within your site as well as the existing events for each person.

Configuration
-------------
This extension is not configurable. Enable it in your site's configuration file as follows:

.. code-block:: yaml

    extensions:
      betty.extension.deriver.Deriver: ~
