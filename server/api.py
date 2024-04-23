"""
Defines the endpoints available for the database API.
"""

from datetime import datetime
from typing import Optional
from flask import request
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import or_

import config

from . import db
from . import models

def teams(year: int) -> Pagination:
    """
    `/api/teams?[year=...&page=...&page_size=...]` :
    Responds with a list of `Team`s, optionally filtered by `year`
    """
    query = db.select(models.Team).order_by(models.Team.id)
    if year is not None:
        query = query.where(models.Team.year == year)
    return db.paginate(query, count=False, max_per_page=config.MAX_PAGE_SIZE)

def team(id: int) -> models.Team:
    """
    `/api/teams/<id>` :
    Responds with the requested `Team`
    """
    team = db.get_or_404(models.Team, int(id))
    return team

def team_members(id: int) -> Pagination:
    """
    `/api/teams/<id>/members[?page=...&page_size=...]` :
    Responds with the `Member`s of the specified `Team`
    """
    query = db\
        .select(models.Player)\
        .join(models.Member)\
        .where(models.Member.team_id == int(id))\
        .order_by(models.Player.id) 
    return db.paginate(query, count=False, max_per_page=config.MAX_PAGE_SIZE)

def players() -> Pagination:
    """
    `/api/players[?page=...&page_size=...]` :
    Responds with a list of `Player`s
    """
    query = (
        db
        .select(models.Player)
        .order_by(models.Player.id)
        .paginate(count=False, max_per_page=config.MAX_PAGE_SIZE)
    )
    return db.paginate(query, count=False, max_per_page=config.MAX_PAGE_SIZE)

def player(id: int) -> models.Player:
    """
    `/api/players/<id>` :
    Responds with the requested `Player`
    """
    player = db.get_or_404(models.Player, int(id))
    return player

def matches() -> Pagination:
    """
    `/api/matches[?before=...&after=...&teamid=...&page=...&page_size=...]` :
    Responds with a list of `Match`es, optionally filtered by date and team
    """
    before: Optional[str] = request.args.get('before')
    after: Optional[str] = request.args.get('after')
    teamid: Optional[str] = request.args.get('teamid')
    query = db.select(models.Match).order_by(models.Match.id) 
    if before:
        query = query.where(models.Match.play_date < int(before))
    if after:
        query = query.where(models.Match.play_date >= int(after))
    if teamid:
        query = query.where(or_(
            models.Match.team1_id == int(teamid),
            models.Match.team2_id == int(teamid)
        ))
    return db.paginate(query, count=False, max_per_page=config.MAX_PAGE_SIZE)

def match(id: int) -> models.Match:
    """
    `/api/match/<id>` :
    Responds with the requested `Match`
    """
    match = db.get_or_404(models.Match, int(id))
    return match

