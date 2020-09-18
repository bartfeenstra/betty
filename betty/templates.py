from typing import Any, Dict


def _build__page__person(vars: Dict[str, Any]) -> None:
    person = vars['person']

    # Get the person's associated events.
    # First, get the person's own events.
    events = [presence.event for presence in person.presences if presence.event.date is not None and presence.event.date.comparable]
    # Then find the events for the person's grandparents, parents partners, children, and grandchildren that fall within
    # the person's lifetime.
    if person.start or person.end:
        associated_people = [
            # Collect grandparents.
            *[grandparent for parent in person.parents for grandparent in parent.parents],
            # Collect parents.
            *person.parents,
            # Collect siblings.
            *[child for parent in person.parents for child in parent.children],
            # Collect partners.
            *[parent for child in person.children for parent in child.parents],
            # Collect children.
            *person.children,
            # Collect grandchildren.
            *[grandchild for child in person.children for grandchild in child.children],
        ]
        # Collect associated events with comparable dates.
        associated_events = [event for person in associated_people for event in (person.start, person.end) if event is not None and event.date is not None and event.date.comparable]
        # Filter out any associated events from before the person's start of life.
        if person.start is not None and person.start.date is not None and person.start.date.comparable:
            associated_events = [event for event in associated_events if event.date >= person.start.date]
        # Filter out any associated events from after the person's end of life.
        if person.end is not None and person.end.date is not None and person.end.date.comparable:
            associated_events = [event for event in associated_events if event.date <= person.end.date]
        events += associated_events
    vars['associated_events'] = set(events)


VARS_BUILDERS = {
    'page/person.html.j2': _build__page__person
}
