from dataclasses import dataclass
from typing import Optional
from .database import CONNECTION
from datetime import date, datetime


# Classes representing entities in the database

@dataclass(frozen=True)
class Team:
    id: int
    name: str
    year: int

@dataclass(frozen=True)
class Player:
    """
    A player who has signed up
    """
    id: int
    name_first: str
    name_last: str

@dataclass(frozen=True)
class Member:
    """
    Represents a player who is part of a team
    """
    player_id: int
    team_id: int

@dataclass(frozen=True)
class Match:
    """
    A match between two teams
    """
    id: int
    team1_id: int
    team2_id: int
    score1: float
    score2: float
    play_date: date


# Enpoints to fetch from the database

def get_all_teams(year: Optional[int] = None) -> list[Team]:
    """
    Fetch all the teams present in the database.
    :param year: Optionally limit results to one year
    """

    sql = [
        "SELECT id, name, year FROM teams"
    ]

    if year is not None:
        sql.append(f"WHERE year={int(year):d}")

    query = CONNECTION.execute(' '.join(sql)).fetchall()
    return [Team(*q) for q in query]

def get_team(id: int) -> Optional[Team]:
    """
    Fetches the team with the given `id`, if it exists.
    """

    sql = "SELECT id, name, year FROM teams WHERE id={:d}".format(int(id))

    query = CONNECTION.execute(sql).fetchone()
    if query is None: return None
    return Team(*query)

def get_all_players() -> list[Player]:
    """
    Fetch all the players present in the database.
    """

    sql = "SELECT id, name_first, name_last FROM players"

    query = CONNECTION.execute(sql).fetchall()
    return [Player(*q) for q in query]

def get_player(id: int) -> Optional[Player]:
    """
    Fetches the player with the given `id`, if they exist.
    """

    sql = "SELECT id, name_first, name_last FROM players WHERE id={:d}".format(int(id))

    query = CONNECTION.execute(sql).fetchone()
    if query is None: return None
    return Player(*query)

def get_all_members(team_id: Optional[int] = None, player_id: Optional[int] = None) -> list[Member]:
    """
    Fetch all the members present in the database.
    :param team_id: Optionally limit results to one team
    :param player_id: Optionally limit results to one player
    """

    sql = "SELECT player_id, team_id FROM members"

    where = []
    if team_id is not None:
        where.append(f"team_id={int(team_id):d}")
    if player_id is not None:
        where.append(f"player_id={int(player_id):d}")
    if where:
        sql += f" WHERE {' AND '.join(where)}"

    query = CONNECTION.execute(sql).fetchall()
    return [Member(*q) for q in query]

def get_all_matches(team_id: Optional[int] = None, before: Optional[date] = None, after: Optional[date] = None) -> list[Match]:
    """
    Fetch all the matches present in the database.
    :param team_id: Optionally limit results to one team
    :param before: Optionally limit results to before this date (exclusive)
    :param after: Optionally limit results to after this date (inclusive)
    """

    sql = "SELECT id, team1_id, team2_id, score1, score2, play_date FROM matches"

    where = []
    if team_id is not None:
        where.append(f"(team1_id={int(team_id):d} OR team2_id={int(team_id):d})")
    if before is not None:
        t = datetime(year=before.year, month=before.month, day=before.day)
        timestamp = int(t.timestamp())
        where.append(f"play_date < {timestamp:d}")
    if after is not None:
        t = datetime(year=after.year, month=after.month, day=after.day)
        timestamp = int(t.timestamp())
        where.append(f"play_date >= {timestamp:d}")
    if where:
        sql += f" WHERE {' AND '.join(where)}"

    query = CONNECTION.execute(sql).fetchall()
    return [Match(*q) for q in query]


def get_match(id: int) -> Optional[Match]:
    """
    Fetches the match with the given `id`, if it exists.
    """

    sql = "SELECT id, team1_id, team2_id, score1, score2, play_date FROM matches WHERE id={:d}".format(int(id))

    query = CONNECTION.execute(sql).fetchone()
    if query is None: return None
    return Match(*query)
