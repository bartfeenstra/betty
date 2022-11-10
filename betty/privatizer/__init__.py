import logging
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from betty.model import Entity

if TYPE_CHECKING:
    from betty.builtins import _

from betty.app.extension import UserFacingExtension
from betty.functools import walk
from betty.load import PostLoader
from betty.locale import DateRange, Date
from betty.model.ancestry import Ancestry, Person, Event, Citation, Source, HasPrivacy, Subject, File, HasFiles, \
    HasCitations


class Privatizer(UserFacingExtension, PostLoader):
    async def post_load(self) -> None:
        privatize(self.app.project.ancestry, self.app.project.configuration.lifetime_threshold)

    @classmethod
    def label(cls) -> str:
        return _('Privatizer')

    @classmethod
    def description(cls) -> str:
        return _('Determine if people can be proven to have died. If not, mark them and their related resources private, but only if they are not already explicitly marked public or private. Enable the Anonymizer and Cleaner as well to make this most effective.')


def privatize(ancestry: Ancestry, lifetime_threshold: int = 125) -> None:
    seen: List[Entity] = []

    privatized = 0
    for person in ancestry.entities[Person]:
        private = person.private
        _privatize_person(person, seen, lifetime_threshold)
        if private is None and person.private is True:
            privatized += 1
    logger = logging.getLogger()
    logger.info('Privatized %d people because they are likely still alive.' % privatized)

    for citation in ancestry.entities[Citation]:
        _privatize_citation(citation, seen)

    for source in ancestry.entities[Source]:
        _privatize_source(source, seen)

    for event in ancestry.entities[Event]:
        _privatize_event(event, seen)

    for file in ancestry.entities[File]:
        _privatize_file(file, seen)


def _mark_private(has_privacy: HasPrivacy) -> None:
    # Do not change existing explicit privacy declarations.
    if has_privacy.private is None:
        has_privacy.private = True


def _privatize_person(person: Person, seen: List[Entity], lifetime_threshold: int) -> None:
    # Do not change existing explicit privacy declarations.
    if person.private is None:
        person.private = _person_is_private(person, lifetime_threshold)

    if not person.private:
        return

    for presence in person.presences:
        if isinstance(presence.role, Subject):
            _mark_private(presence.event)
            _privatize_event(presence.event, seen)

    _privatize_has_citations(person, seen)
    _privatize_has_files(person, seen)


def _privatize_event(event: Event, seen: List[Entity]) -> None:
    if not event.private:
        return

    if event in seen:
        return
    seen.append(event)

    _privatize_has_citations(event, seen)
    _privatize_has_files(event, seen)


def _privatize_has_citations(has_citations: HasCitations, seen: List[Entity]) -> None:
    for citation in has_citations.citations:
        _mark_private(citation)
        _privatize_citation(citation, seen)


def _privatize_citation(citation: Citation, seen: List[Entity]) -> None:
    if not citation.private:
        return

    if citation in seen:
        return
    seen.append(citation)

    _mark_private(citation.source)
    _privatize_source(citation.source, seen)
    _privatize_has_files(citation, seen)


def _privatize_source(source: Source, seen: List[Entity]) -> None:
    if not source.private:
        return

    if source in seen:
        return
    seen.append(source)

    _privatize_has_files(source, seen)


def _privatize_has_files(has_files: HasFiles, seen: List[Entity]) -> None:
    for file in has_files.files:
        _mark_private(file)
        _privatize_file(file, seen)


def _privatize_file(file: File, seen: List[Entity]) -> None:
    if not file.private:
        return

    if file in seen:
        return
    seen.append(file)

    _privatize_has_citations(file, seen)


def _person_is_private(person: Person, lifetime_threshold: int) -> bool:
    # A dead person is not private, regardless of when they died.
    if person.end is not None:
        if person.end.date is None:
            return False
        if _event_has_expired(person.end, lifetime_threshold, 0):
            return False

    if _person_has_expired(person, lifetime_threshold, 1):
        return False

    def ancestors(person: Person, generation: int = -1):
        for parent in person.parents:
            yield generation, parent
            yield from ancestors(parent, generation - 1)

    for generation, ancestor in ancestors(person):
        if _person_has_expired(ancestor, lifetime_threshold, abs(generation) + 1):
            return False

    # If any descendant has any expired event, the person is considered not private.
    for descendant in walk(person, 'children'):
        if _person_has_expired(descendant, lifetime_threshold, 1):
            return False

    return True


def _person_has_expired(person: Person, lifetime_threshold: int, multiplier: int) -> bool:
    for presence in person.presences:
        if _event_has_expired(presence.event, lifetime_threshold, multiplier):
            return True
    return False


def _event_has_expired(event: Event, lifetime_threshold: int, multiplier: int) -> bool:
    assert multiplier >= 0

    date = event.date

    if isinstance(date, DateRange):
        # We can only determine event expiration with certainty if we have an end date to work with. Someone born in
        # 2000 can have a valid birth event with a start date of 1800, which does nothing to help us determine
        # expiration.
        date = date.end

    return _date_has_expired(date, lifetime_threshold, multiplier)


def _date_has_expired(date: Optional[Date], lifetime_threshold: int, multiplier: int) -> bool:
    assert multiplier >= 0

    if date is None:
        return False

    if not date.comparable:
        return False

    return date <= Date(datetime.now().year - lifetime_threshold * multiplier, datetime.now().month, datetime.now().day)
