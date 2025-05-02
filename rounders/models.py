"""
Data models to represent entities in the database
"""

from __future__ import annotations

from functools import cached_property
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, or_
from dataclasses import dataclass

from . import db, app


@dataclass(frozen=True)
class Score:
    """A match result, from the POV of a given 'home' team"""
    home: Optional[float]
    away: Optional[float]


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

    @cached_property
    def matches(self) -> list[Match]:
        return db.session.scalars(
            db.select(Match).where(
                or_(Match.team1_id == self.id, Match.team2_id == self.id)
            )
        ).all()
 
    @cached_property
    def num_matches_played(self) -> int:
        return len([m for m in self.matches if m.played])

    @cached_property
    def num_wins(self) -> int:
        return len([m for m in self.matches if m.winner and m.winner.id == self.id])

    @cached_property
    def num_draws(self) -> int:
        return len([m for m in self.matches if m.played and m.winner is None])

    @cached_property
    def num_losses(self) -> int:
        return len([m for m in self.matches if m.winner and m.winner.id != self.id])

    @cached_property
    def num_points(self) -> int:
        return 2 * self.num_wins + self.num_draws

    @cached_property
    def num_rounders_scored(self) -> float:
        return sum([m.pov_score(self).home or 0 for m in self.matches if m.played])

    @cached_property
    def num_rounders_conceded(self) -> float:
        return sum([m.pov_score(self).away or 0 for m in self.matches if m.played])

    @cached_property
    def net_rounders(self) -> float:
        return self.num_rounders_scored - self.num_rounders_conceded


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
    id:         Mapped[int]   = mapped_column(primary_key=True, nullable=False)
    team1_id:   Mapped[int]   = mapped_column(ForeignKey('teams.id'), nullable=False)
    team2_id:   Mapped[int]   = mapped_column(ForeignKey('teams.id'), nullable=False)
    score1:     Mapped[Optional[float]] = mapped_column(nullable=True)
    score2:     Mapped[Optional[float]] = mapped_column(nullable=True)
    score1_in1: Mapped[Optional[float]] = mapped_column(nullable=True)
    """Points scored by team 1 in the first inning, may be null even if score1 is not null"""
    score2_in1: Mapped[Optional[float]] = mapped_column(nullable=True)
    """Points scored by team 2 in the first inning, may be null even if score2 is not null"""
    play_date:  Mapped[Optional[int]]   = mapped_column(nullable=True)
    """Unix epoch of the start of the date played on"""

    # Relationships
    team1: Mapped["Team"] = relationship(foreign_keys="Match.team1_id", back_populates="matches1")
    """The first team of this match"""
    team2: Mapped["Team"] = relationship(foreign_keys="Match.team2_id", back_populates="matches2")
    """The second team of this match"""

    @property
    def score1_in2(self) -> Optional[float]:
        """Points scored by team 1 in the second inning, may be null even if score1 is not null"""
        return (
            self.score1 - self.score1_in1
            if not (self.score1 is None or self.score1_in1 is None)
            else None
        )

    @property
    def score2_in2(self) -> Optional[float]:
        """Points scored by team 2 in the second inning, may be null even if score2 is not null"""
        return (
            self.score2 - self.score2_in1
            if not (self.score2 is None or self.score2_in1 is None)
            else None
        )

    @property
    def winner(self) -> Optional[Team]:
        """The winning team, if has been played and not a draw"""
        s1 = -1 if self.score1 is None else self.score1
        s2 = -1 if self.score2 is None else self.score2
        if s1 == s2: return None
        return self.team1 if s1 > s2 else self.team2

    @property
    def played(self) -> bool:
        """Whether the match has been played or not"""
        return self.score1 != None or self.score2 != None

    def pov_score(self, team: Team) -> Score:
        """The result, from the POV of the given team"""
        if team.id == self.team1_id:
            return Score(home=self.score1, away=self.score2)
        elif team.id == self.team2_id:
            return Score(home=self.score2, away=self.score1)
        else:
            raise Exception("Not a valid team to view match as")

    def opponent_of(self, team: Team) -> Team:
        """The opponent of the given team"""
        if team.id == self.team1_id:
            return self.team2
        elif team.id == self.team2_id:
            return self.team1
        else:
            raise Exception("Not a valid team to view match as")

    @classmethod
    def score_from_innings(cls, inning1: Optional[float], inning2: Optional[float]) -> Optional[float]:
            """Compute total score, given score (if any) achieved during each inning"""

            # Total score is NULL if both innings are NULL.
            # If either inning is NOT NULL, the total score is NOT NULL.
            return (
                None
                if (inning1 is None and inning2 is None)
                else (inning1 or 0) + (inning2 or 0)
            )

# Create all the tables based on these models
with app.app_context():
    db.create_all()
