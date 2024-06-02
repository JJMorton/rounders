from datetime import datetime, UTC

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
import functools
from typing import Any, Optional

from .models import Team

@functools.total_ordering
class FormatAs(ABC):
    """
    A field that can be sorted by `._sort_value`,
    grouped by `._group_value`, and displayed as
    per `._name`.
    Note: Do not inherit with a dataclass, as this
    overrides the needed `.__hash__()` method.
    """

    def __init__(self, sort_reverse: bool = False) -> None:
        self._reverse = sort_reverse

    @property
    @abstractmethod
    def _sort_value(self) -> Any:
        """Value to sort the items by"""

    @property
    @abstractmethod
    def _group_value(self) -> Any:
        """Value to group the items by"""

    @property
    @abstractmethod
    def _name(self) -> str:
        """Text used to display each item"""

    def __str__(self) -> str:
        return self._name

    # This might require explanation.
    # To group items, they will be compared against
    # each other with the '==' or 'is' operators,
    # so those methods must return the value to
    # group by.
    # In Python 3.x, sorting is done entirely with
    # the '<' operator, so we only need to use the
    # sort value in that.

    def __hash__(self) -> Any:
        return hash(self._group_value)

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._group_value == other._group_value

    def __lt__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        if self._reverse:
            return self._sort_value > other._sort_value
        else:
            return self._sort_value < other._sort_value


class AsScore(FormatAs):

    def __init__(self, score: Optional[float], sort_reverse: bool = False):
        self.score = score
        super().__init__(sort_reverse=sort_reverse)

    @property
    def _sort_value(self) -> float:
        return -1 if self.score is None else self.score

    @property
    def _group_value(self) -> Optional[float]:
        return self._sort_value

    @property
    def _name(self) -> str:
        if self.score is None:
            return '--'
        else:
            return f'{self.score:.1f}'


class AsDateTime(FormatAs):
    """A datetime with custom formatting"""

    def __init__(self, timestamp: Optional[int], fmt: str, newest_first: bool = True):
        self.timestamp = timestamp
        self.fmt = fmt
        super().__init__(newest_first)

    @property
    def _sort_value(self) -> Optional[int]:
        return -1 if self.timestamp is None else self.timestamp

    @property
    def _group_value(self) -> Any:
        return self._name

    @property
    def _name(self) -> str:
        if self.timestamp is None: return ''
        return datetime.fromtimestamp(self.timestamp, UTC).strftime(self.fmt)

class AsDate(AsDateTime):

    def __init__(self, timestamp: Optional[int], newest_first: bool = True):
        super().__init__(timestamp, '%a %d %b', newest_first=newest_first)

    @property
    def _name(self) -> str:
        if self.timestamp is None: return 'TBC'
        return super()._name

class AsTime(AsDateTime):

    def __init__(self, timestamp: Optional[int], newest_first: bool = True):
        super().__init__(timestamp, '%H:%M', newest_first=newest_first)

class AsDateInput(AsDateTime):
    """Formats a date for an `<input type="date">` HTML element"""

    def __init__(self, timestamp: Optional[int]):
        super().__init__(timestamp, '%Y-%m-%d')

class AsTimeInput(AsDateTime):
    """Formats a time for an `<input type="time">` HTML element"""

    def __init__(self, timestamp: Optional[int]):
        super().__init__(timestamp, '%H:%M')

class AsWeekOf(AsDate):
    """Represents the start of the week containing `timestamp`"""

    def __init__(self, timestamp: Optional[int], newest_first: bool = True):
        if timestamp == None:
            return super().__init__(None, newest_first=newest_first)
        else:
            d = datetime.fromtimestamp(timestamp)
            monday = d - timedelta(days = d.weekday())
            ts = int(datetime(monday.year, monday.month, monday.day, tzinfo=UTC).timestamp())
            super().__init__(ts, newest_first=newest_first)

    @property
    def _name(self) -> str:
        if self.timestamp is None: return 'Date TBC'
        return 'Week of ' + super()._name


class AsTeamName(FormatAs):
    """Allow sorting/grouping by team"""

    def __init__(self, team: Optional[Team], sort_reverse: bool = False):
        self.team = team
        super().__init__(sort_reverse)

    @property
    def _group_value(self) -> int:
        if self.team is None:
            return -1
        return self.team.id

    @property
    def _sort_value(self) -> str:
        if self.team is None:
            return ""
        return self.team.name

    @property
    def _name(self) -> str:
        if self.team is None:
            return "Unknown"
        return self.team.name


def basic_sanitisation(s: str) -> str:
    """
    Very basic sanitisation, just to prevent mistakes.
    Doesn't need to be elaborate, as long as I'm aware of where
    the string is being used.
    """
    forbid_chars = ['\\', '\'', '"', ';', '<', '>']
    return ''.join(ch for ch in s if not ch in forbid_chars)
