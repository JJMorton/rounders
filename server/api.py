"""
Defines the endpoints available for the database API.
"""

from typing import Optional
from flask import Response, jsonify, request
from sqlalchemy import or_

from . import app
from . import db
from . import models

@app.route('/api/teams')
def api_teams() -> Response:
    """
    `/api/teams?[year=...]` :
    Responds with a list of `Team`s, optionally filtered by `year`
    """
    year: Optional[str] = request.args.get('year')
    query = db.select(models.Team).order_by(models.Team.id)
    if year is not None:
        query = query.where(models.Team.year == int(year))
    teams = db.session.execute(query).scalars().all()
    return jsonify(teams)

@app.route('/api/teams/<int:id>')
def api_team(id: int) -> Response:
    """
    `/api/teams/<id>` :
    Responds with the requested `Team`
    """
    team = db.get_or_404(models.Team, int(id))
    return jsonify(team)

@app.route('/api/teams/<int:id>/players')
def api_team_members(id: int) -> Response:
    """
    `/api/teams/<id>/members` :
    Responds with the `Member`s of the specified `Team`
    """
    query = db\
        .select(models.Player)\
        .join(models.Member)\
        .where(models.Member.team_id == int(id))\
        .order_by(models.Player.id) 
    members = db.session.execute(query).scalars().all()
    return jsonify(members)

@app.route('/api/players')
def api_players() -> Response:
    """
    `/api/players` :
    Responds with a list of `Player`s
    """
    query = db.select(models.Player).order_by(models.Player.id) 
    players = db.session.execute(query).scalars().all()
    return jsonify(players)

@app.route('/api/players/<int:id>')
def api_player(id: int) -> Response:
    """
    `/api/players/<id>` :
    Responds with the requested `Player`
    """
    player = db.get_or_404(models.Player, int(id))
    return jsonify(player)

@app.route('/api/matches')
def api_matches() -> Response:
    """
    `/api/matches[?before=...&after=...&teamid=...` :
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
    matches = db.session.execute(query).scalars().all()
    return jsonify(matches)

@app.route('/api/matches/<int:id>')
def api_match(id: int) -> Response:
    """
    `/api/match/<id>` :
    Responds with the requested `Match`
    """
    match = db.get_or_404(models.Match, int(id))
    return jsonify(match)
