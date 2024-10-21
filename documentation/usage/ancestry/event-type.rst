Event Type
==========

:doc:`Event </usage/ancestry/event>` types are what indicate what kind of thing an event is about, such as a birth, death, or marriage.
They inherit from :py:class:`betty.ancestry.event_type.event_types.EventType`.

Built-in event types
--------------------
``adoption`` (:py:class:`betty.ancestry.event_type.event_types.Adoption`)
    A person's `adoption <https://en.wikipedia.org/wiki/Adoption>`_.
``baptism`` (:py:class:`betty.ancestry.event_type.event_types.Baptism`)
    A person's `baptism <https://en.wikipedia.org/wiki/Baptism>`_.
``bar-mitzvah`` (:py:class:`betty.ancestry.event_type.event_types.BarMitzvah`)
    A person's `bar mitzvah <https://en.wikipedia.org/wiki/Bar_and_bat_mitzvah>`_.
``bat-mitzvah`` (:py:class:`betty.ancestry.event_type.event_types.BatMitzvah`)
    A person's `bat mitzvah <https://en.wikipedia.org/wiki/Bar_and_bat_mitzvah>`_.
``birth`` (:py:class:`betty.ancestry.event_type.event_types.Birth`)
    A person's birth. This event type often receives special treatment and is considered the authoritative
    type to determine when somebody's life started.
``burial`` (:py:class:`betty.ancestry.event_type.event_types.Burial`)
    A person's `burial <https://en.wikipedia.org/wiki/Burial>`_.
``conference`` (:py:class:`betty.ancestry.event_type.event_types.Conference`)
    A `conference <https://en.wikipedia.org/wiki/Conference>`_.
``confirmation`` (:py:class:`betty.ancestry.event_type.event_types.Confirmation`)
    A `christian confirmation <https://en.wikipedia.org/wiki/Confirmation>`_.
``correspondence`` (:py:class:`betty.ancestry.event_type.event_types.Correspondence`)
    Correspondence between people, such as letters or emails.
``cremation`` (:py:class:`betty.ancestry.event_type.event_types.Cremation`)
    A person's `cremation <https://en.wikipedia.org/wiki/Cremation>`_.
``death`` (:py:class:`betty.ancestry.event_type.event_types.Death`)
    A person's death. This event type often receives special treatment and is considered the authoritative
    type to determine when somebody's life ended.
``divorce`` (:py:class:`betty.ancestry.event_type.event_types.Divorce`)
    A person's `divorce <https://en.wikipedia.org/wiki/Divorce>`_ from another.
``divorce-announcement`` (:py:class:`betty.ancestry.event_type.event_types.DivorceAnnouncement`)
    The public announcement of a person's `divorce <https://en.wikipedia.org/wiki/Divorce>`_ from another.
``emigration`` (:py:class:`betty.ancestry.event_type.event_types.Emigration`)
    A person's `emigration <https://en.wikipedia.org/wiki/Emigration>`_ from a place.
``engagement`` (:py:class:`betty.ancestry.event_type.event_types.Engagement`)
    A person's `engagement <https://en.wikipedia.org/wiki/Engagement>`_ to another.
``funeral`` (:py:class:`betty.ancestry.event_type.event_types.Funeral`)
    A person's `funeral <https://en.wikipedia.org/wiki/Funeral>`_.
``immigration`` (:py:class:`betty.ancestry.event_type.event_types.Immigration`)
    A person's `immigration <https://en.wikipedia.org/wiki/Immigration>`_ to a place.
``marriage`` (:py:class:`betty.ancestry.event_type.event_types.Marriage`)
    A person's `marriage <https://en.wikipedia.org/wiki/Marriage>`_ to another.
``marriage-announcement`` (:py:class:`betty.ancestry.event_type.event_types.MarriageAnnouncement`)
    The public announcement of a person's `marriage <https://en.wikipedia.org/wiki/Marriage>`_ to another, such as `marriage banns <https://en.wikipedia.org/wiki/Banns_of_marriage>`_.
``missing`` (:py:class:`betty.ancestry.event_type.event_types.Missing`)
    When someone has become a `missing person <https://en.wikipedia.org/wiki/Missing_person>`_.
``occupation`` (:py:class:`betty.ancestry.event_type.event_types.Occupation`)
    How a person spends their time in society, such as through employment or education.
``residence`` (:py:class:`betty.ancestry.event_type.event_types.Residence`)
    A person stayed or lived in a place for some time.
``retirement`` (:py:class:`betty.ancestry.event_type.event_types.Retirement`)
    A person's `retirement <https://en.wikipedia.org/wiki/Retirement>`_ from their occupations.
``unknown`` (:py:class:`betty.ancestry.event_type.event_types.Unknown`)
    The event's type is not otherwise known.
``will`` (:py:class:`betty.ancestry.event_type.event_types.Will`)
    Any event associated with the reading and excution of someone's `will and testament <https://en.wikipedia.org/wiki/Will_and_testament>`_.

Built-in meta event types
-------------------------
The aforementioned event types can inherit from these meta types. For example, births and baptisms are both start-of-life events.

:py:class:`betty.ancestry.event_type.event_types.StartOfLifeEventType`
    Any event taking place because of and close to someone's birth, such as a baptism, or an actual birth.
:py:class:`betty.ancestry.event_type.event_types.DuringLifeEventType`
    Any event taking place while the subject was still alive, e.g. between their birth and death.
:py:class:`betty.ancestry.event_type.event_types.EndOfLifeEventType`
    Any event taking place because of and close to someone's death, such as a funeral, or an actual death.
:py:class:`betty.ancestry.event_type.event_types.PostDeathEventType`
    Any event taking place after someone's death, such as a funeral or will reading.
:py:class:`betty.ancestry.event_type.event_types.FinalDispositionEventType`
    Any `final disposition <https://en.wikipedia.org/wiki/Final_disposition>`_, such as a burial or cremation.

See also
--------
- :doc:`/development/plugin/event-type`
