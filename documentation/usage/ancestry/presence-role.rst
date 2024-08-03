Presence Role
=============

:doc:`Presence </usage/ancestry/presence>` roles are what indicate how a person was involved with an event, such as a subject, a witness, or a regular attendee.
They inherit from :py:class:`betty.ancestry.presence_role.PresenceRole`.

Built-in presence roles
-----------------------
:py:class:`betty.ancestry.presence_role.Subject`
    The person was a primary subject at the event, such as the person being born at a birth, or one of the happy couple at a wedding.
:py:class:`betty.ancestry.presence_role.Witness`
    The person was a witness at an event where other people were the subjects.
:py:class:`betty.ancestry.presence_role.Beneficiary`
    The person was the event's beneficiary, such as when a will was read.
:py:class:`betty.ancestry.presence_role.Attendee`
    The person was an attendee at the event and no additional details about their involvement are known.
:py:class:`betty.ancestry.presence_role.Speaker`
    The person performed public speaking at the event.
:py:class:`betty.ancestry.presence_role.Celebrant`
    The person was the celebrant or officiant at the event, such as a civil servant or a clergyperson.
:py:class:`betty.ancestry.presence_role.Organizer`
    The person organized the event.

See also
--------
- :doc:`/development/plugin/presence-role`
