"""
Data models to represent entities in the database
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey

from . import db, app

class Team(db.Model):
    """
    A team of players
    """
    __tablename__ = "teams"
    id:   Mapped[int] = mapped_column(primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)

class Player(db.Model):
    """
    A player who has signed up, can be in any number of teams
    """
    __tablename__ = "players"
    id:         Mapped[int] = mapped_column(primary_key=True, nullable=False)
    name_first: Mapped[str] = mapped_column(nullable=False)
    name_last:  Mapped[str] = mapped_column(nullable=False)

class Member(db.Model):
    """
    Represents a player as part of a team
    """
    __tablename__ = "members"
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), primary_key=True, nullable=False)
    team_id:   Mapped[int] = mapped_column(ForeignKey('teams.id'), primary_key=True, nullable=False)

class Match(db.Model):
    """
    A match between two teams
    """
    __tablename__ = "matches"
    id:        Mapped[int]   = mapped_column(primary_key=True, nullable=False)
    team1_id:  Mapped[int]   = mapped_column(ForeignKey('teams.id'), nullable=False)
    team2_id:  Mapped[int]   = mapped_column(ForeignKey('teams.id'), nullable=False)
    score1:    Mapped[float] = mapped_column(nullable=True)
    score2:    Mapped[float] = mapped_column(nullable=True)
    play_date: Mapped[int]   = mapped_column(nullable=True)
    """Unix epoch of the start of the date played on"""


# Create all the tables based on these models
with app.app_context():
    db.create_all()
