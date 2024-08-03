Event Type
==========

:doc:`Event </usage/ancestry/event>` types are what indicate what kind of thing an event is about, such as a birth, death, or marriage.
They inherit from :py:class:`betty.ancestry.event_type.EventType`.

Built-in event types
--------------------
:py:class:`betty.ancestry.event_type.Adoption`
    A person's `adoption <https://en.wikipedia.org/wiki/Adoption>`_.
:py:class:`betty.ancestry.event_type.Baptism`
    A person's `baptism <https://en.wikipedia.org/wiki/Baptism>`_.
:py:class:`betty.ancestry.event_type.Birth`
    A person's birth. This event type often receives special treatment and is considered the authoritative
    type to determine when somebody's life started.
:py:class:`betty.ancestry.event_type.Burial`
    A person's `burial <https://en.wikipedia.org/wiki/Burial>`_.
:py:class:`betty.ancestry.event_type.Conference`
    A `conference <https://en.wikipedia.org/wiki/Conference>`_.
:py:class:`betty.ancestry.event_type.Confirmation`
    A `christian confirmation <https://en.wikipedia.org/wiki/Confirmation>`_.
:py:class:`betty.ancestry.event_type.Correspondence`
    Correspondence between people, such as letters or emails.
:py:class:`betty.ancestry.event_type.Cremation`
    A person's `cremation <https://en.wikipedia.org/wiki/Cremation>`_.
:py:class:`betty.ancestry.event_type.Death`
    A person's death. This event type often receives special treatment and is considered the authoritative
    type to determine when somebody's life ended.
:py:class:`betty.ancestry.event_type.Divorce`
    A person's `divorce <https://en.wikipedia.org/wiki/Divorce>`_ from another.
:py:class:`betty.ancestry.event_type.DivorceAnnouncement`
    The public announcement of a person's `divorce <https://en.wikipedia.org/wiki/Divorce>`_ from another.
:py:class:`betty.ancestry.event_type.Emigration`
    A person's `emigration <https://en.wikipedia.org/wiki/Emigration>`_ from a place.
:py:class:`betty.ancestry.event_type.Engagement`
    A person's `engagement <https://en.wikipedia.org/wiki/Engagement>`_ to another.
:py:class:`betty.ancestry.event_type.Funeral`
    A person's `funeral <https://en.wikipedia.org/wiki/Funeral>`_.
:py:class:`betty.ancestry.event_type.Immigration`
    A person's `immigration <https://en.wikipedia.org/wiki/Immigration>`_ to a place.
:py:class:`betty.ancestry.event_type.Marriage`
    A person's `marriage <https://en.wikipedia.org/wiki/Marriage>`_ to another.
:py:class:`betty.ancestry.event_type.MarriageAnnouncement`
    The public announcement of a person's `marriage <https://en.wikipedia.org/wiki/Marriage>`_ to another, such as `marriage banns <https://en.wikipedia.org/wiki/Banns_of_marriage>`_.
:py:class:`betty.ancestry.event_type.Missing`
    When someone has become a `missing person <https://en.wikipedia.org/wiki/Missing_person>`_.
:py:class:`betty.ancestry.event_type.Occupation`
    How a person spends their time in society, such as through employment or education.
:py:class:`betty.ancestry.event_type.Residence`
    A person stayed or lived in a place for some time.
:py:class:`betty.ancestry.event_type.Retirement`
    A person's `retirement <https://en.wikipedia.org/wiki/Retirement>`_ from their occupations.
:py:class:`betty.ancestry.event_type.UnknownEventType`
    The event's type is not otherwise known.
:py:class:`betty.ancestry.event_type.Will`
    Any event associated with the reading and excution of someone's `will and testament <https://en.wikipedia.org/wiki/Will_and_testament>`_.

Built-in meta event types
-------------------------
The aforementioned event types can inherit from these meta types. For example, births and baptisms are both start-of-life events.

:py:class:`betty.ancestry.event_type.StartOfLifeEventType`
    Any event taking place because of and close to someone's birth, such as a baptism, or an actual birth.
:py:class:`betty.ancestry.event_type.DuringLifeEventType`
    Any event taking place while the subject was still alive, e.g. between their birth and death.
:py:class:`betty.ancestry.event_type.EndOfLifeEventType`
    Any event taking place because of and close to someone's death, such as a funeral, or an actual death.
:py:class:`betty.ancestry.event_type.PostDeathEventType`
    Any event taking place after someone's death, such as a funeral or will reading.
:py:class:`betty.ancestry.event_type.FinalDispositionEventType`
    Any `final disposition <https://en.wikipedia.org/wiki/Final_disposition>`_, such as a burial or cremation.

See also
--------
- :doc:`/development/plugin/event-type`
