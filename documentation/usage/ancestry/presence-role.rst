Presence Role
=============

:doc:`Presence </usage/ancestry/presence>` roles are what indicate how a person was involved with an event, such as a subject, a witness, or a regular attendee.
They inherit from :py:class:`betty.ancestry.presence_role.PresenceRole`.

Built-in presence roles
-----------------------
``attendee`` (:py:class:`betty.ancestry.presence_role.presence_roles.Attendee`)
    The person was an attendee at the event and no additional details about their involvement are known.
``beneficiary`` (:py:class:`betty.ancestry.presence_role.presence_roles.Beneficiary`)
    The person was the event's beneficiary, such as when a will was read.
``celebrant`` (:py:class:`betty.ancestry.presence_role.presence_roles.Celebrant`)
    The person was the celebrant or officiant at the event, such as a civil servant or a clergyperson.
``informant`` (:py:class:`betty.ancestry.presence_role.presence_roles.Informant`)
    The person was the informant of an event, e.g. they reported it with a record-keeping institution.
``organizer`` (:py:class:`betty.ancestry.presence_role.presence_roles.Organizer`)
    The person organized the event.
``speaker`` (:py:class:`betty.ancestry.presence_role.presence_roles.Speaker`)
    The person performed public speaking at the event.
``subject`` (:py:class:`betty.ancestry.presence_role.presence_roles.Subject`)
    The person was a primary subject at the event, such as the person being born at a birth, or one of the happy couple at a wedding.
``unknown`` (:py:class:`betty.ancestry.presence_role.presence_roles.Unknown`)
    The person's role in the event is unknown.
``witness`` (:py:class:`betty.ancestry.presence_role.presence_roles.Witness`)
    The person was a witness at an event where other people were the subjects.

See also
--------
- :doc:`/development/plugin/presence-role`
