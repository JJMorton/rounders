"""
Data models to represent entities in the database
"""

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from . import db, app


class Team(db.Model):
    """
    A team of players
    """
    __tablename__ = "teams"

    # Columns
    id:   Mapped[int] = mapped_column(primary_key=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)

    # Relationships
    matches1: Mapped[list["Match"]] = relationship(foreign_keys="Match.team1_id", back_populates="team1", lazy="dynamic")
    """Matches in which this was the first team"""
    matches2: Mapped[list["Match"]] = relationship(foreign_keys="Match.team2_id", back_populates="team2", lazy="dynamic")
    """Matches in which this was the second team"""
    players: Mapped[list["Player"]] = relationship(foreign_keys="Player.team_id", back_populates="team", lazy="dynamic")
    """Members of this team"""


class Player(db.Model):
    """
    A player who has signed up, can be in any number of teams
    """
    __tablename__ = "players"

    # Columns
    id:         Mapped[int] = mapped_column(primary_key=True, nullable=False)
    team_id:    Mapped[int] = mapped_column(ForeignKey('teams.id'), nullable=False)
    name_first: Mapped[str] = mapped_column(nullable=False)
    name_last:  Mapped[str] = mapped_column(nullable=False)

    # Relationships
    team: Mapped["Team"] = relationship(back_populates="players")
    """The team which the player is a part of"""


class Match(db.Model):
    """
    A match between two teams
    """
    __tablename__ = "matches"

    # Columns
    id:        Mapped[int]   = mapped_column(primary_key=True, nullable=False)
    team1_id:  Mapped[int]   = mapped_column(ForeignKey('teams.id'), nullable=False)
    team2_id:  Mapped[int]   = mapped_column(ForeignKey('teams.id'), nullable=False)
    score1:    Mapped[float] = mapped_column(nullable=True)
    score2:    Mapped[float] = mapped_column(nullable=True)
    play_date: Mapped[int]   = mapped_column(nullable=True)
    """Unix epoch of the start of the date played on"""

    # Relationships
    team1: Mapped["Team"] = relationship(foreign_keys="Match.team1_id", back_populates="matches1")
    """The first team of this match"""
    team2: Mapped["Team"] = relationship(foreign_keys="Match.team2_id", back_populates="matches2")
    """The second team of this match"""


# Create all the tables based on these models
with app.app_context():
    db.create_all()
