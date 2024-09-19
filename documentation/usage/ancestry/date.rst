Dates
=====

Dates can be expressed in three different ways: :py:class:`Date <betty.date.Date>`,
:py:class:`DateRange <betty.date.DateRange>`, and
:py:class:`Datey <betty.date.Datey>` (which are either dates or date ranges).

Dates
-----
Fields
^^^^^^
``year`` (optional ``int``)
    The date's year as a four-digit number.
``month`` (optional ``int``)
    The date's month as a two-digit number.
``day`` (optional ``int``)
    The date's day as a two-digit number.
``fuzzy`` (``bool``)
    Whether or not the date is fuzzy.

Date ranges
-----------
Fields
^^^^^^
``start`` (optional date)
    The range's start date.
``start_is_boundary`` (``bool``)
    Whether the start date is a boundary.
``end`` (optional date)
    The range's end date.
``end_is_boundary`` (``bool``)
    Whether the end date is a boundary.
