from dataclasses import dataclass
from typing import Optional
from .database import CONNECTION

@dataclass(frozen=True)
class Team:
    id: int
    name: str
    year: int

def get_all_teams(year: Optional[int] = None) -> list[Team]:
    """
    Fetch all the teams present in the database
    :param year: Optionally limit results to one year
    """

    sql = [
        "SELECT id, name, year FROM teams"
    ]

    if year is not None:
        sql.append(f"WHERE year={int(year)}")

    query = CONNECTION.execute(' '.join(sql)).fetchall()
    return [Team(*q) for q in query]
