"""
Defines the endpoints available (i.e. the valid paths that users can make requests to),
and their responses.
"""

from datetime import datetime
from flask import render_template, request
import pandas as pd
from sqlalchemy import and_
from sqlalchemy.orm import aliased

from .models import Team, Player, Member, Match
from . import app
from . import config
from . import db

@app.route('/')
def home():
    return render_template('home/index.html', title='Home')

@app.route('/teams')
def route_teams():
    # Get a list of all teams

    # Get a list of available years
    years = sorted(db.session.execute(db.select(Team.year).distinct()).scalars().all())
    if not years: years.append(datetime.now().year)

    # Use the year specified in the query parameters,
    # otherwise use the latest available year
    year: int = request.args.get('year', default=years[-1], type=int)

    # Fetch the teams
    teams = db.session.scalars(
        db
        .select(Team)
        .where(Team.year == year)
        .order_by(Team.id)
    ).all()

    matches1 = [team.matches1.all() for team in teams]
    matches2 = [team.matches2.all() for team in teams]

    # Create table of teams, total scores and play count, sorting by score
    teams_df = pd.DataFrame(dict(
        id          = [t.id for t in teams],
        name        = [t.name for t in teams],
        match_count = [len(m1) + len(m2) for m1, m2 in zip(matches1, matches2)],
        score       = [
            sum(m.score1 or 0 for m in m1) + sum(m.score2 or 0 for m in m2)
            for m1, m2 in zip(matches1, matches2)
        ]
    )).sort_values('score')

    return render_template(
        'teams/index.html',
        title = f'Teams of {year}',
        teams = teams_df,
        year  = year,
        years = years,
    )

@app.route('/teams/<int:id>')
def route_team(id: int):
    team = db.get_or_404(Team, int(id))

    # Get all player names
    players = db.session.scalars(
        db.select(Player).join(team.members.subquery())
    ).all()

    # Get (score1, score2) from matches where this was team1
    q1 = team.matches1.subquery()
    select1 = db.select(
        Team.id,
        Team.name,
        q1.c.play_date,
        q1.c.score1,
        q1.c.score2
    ).join(Team, Team.id == q1.c.team2_id)

    # Get (score2, score1) from matches where this was team2
    q2 = team.matches2.subquery()
    select2 = db.select(
        Team.id,
        Team.name,
        q2.c.play_date,
        q2.c.score1,
        q2.c.score2
    ).join(Team, Team.id == q2.c.team1_id)

    # Sort by date, put unscheduled matches at the top (newest)
    matches = sorted(
        list(db.session.execute(select1).fetchall()) + list(db.session.execute(select2).fetchall()),
        key=lambda m: m[2] or datetime.now().timestamp() * 2,
        reverse=True,
    )

    matches_df = pd.DataFrame(dict(
        date   = [
            datetime.fromtimestamp(m.play_date).strftime('%d %b')
            if m.play_date != None else 'TBC'
            for m in matches
        ],
        name1  = [team.name] * len(matches),
        name2  = [m.name for m in matches],
        id1    = [team.id] * len(matches),
        id2    = [m.id for m in matches],
        score1 = [m.score1 if m.score1 != None else '--' for m in matches],
        score2 = [m.score2 if m.score2 != None else '--' for m in matches],
        played = [m.score1 != None or m.score2 != None for m in matches],
    ))

    players_df = pd.DataFrame(dict(
        name_first = [p.name_first for p in players],
        name_last  = [p.name_last for p in players],
    ))

    return render_template(
        'teams/team.html',
        title   = f'Team "{team.name}"',
        team    = team,
        matches = matches_df,
        players = players_df,
    )

@app.route('/matches')
def route_matches():

    # Get a list of available years
    years = sorted(db.session.execute(db.select(Team.year).distinct()).scalars().all())
    if not years: years.append(datetime.now().year)

    # Use the year specified in the query parameters,
    # otherwise use the latest available year
    year: int = request.args.get('year', default=years[-1], type=int)

    # Fetch the matches
    # Decide which belong to this year by the teams in them,
    # rather than the date of the match.
    team1 = aliased(Team)
    team2 = aliased(Team)
    matches = db.session.execute(
        db
        .select(Match, team1, team2)
        .join(team1, team1.id == Match.team1_id)
        .join(team2, team2.id == Match.team2_id)
        .filter(and_(team1.year == year, team2.year == year))
    ).fetchall()

    # Sort by date, put unscheduled matches at the top (newest)
    matches = sorted(
        matches,
        key=lambda m: m[0].play_date or datetime.now().timestamp() * 2,
        reverse=True,
    )

    matches_df = pd.DataFrame(dict(
        date   = [
            datetime.fromtimestamp(m[0].play_date).strftime('%d %b')
            if m[0].play_date != None else 'TBC'
            for m in matches
        ],
        name1  = [m[1].name for m in matches],
        name2  = [m[2].name for m in matches],
        id1    = [m[1].id for m in matches],
        id2    = [m[2].id for m in matches],
        score1 = [m[0].score1 if m[0].score1 != None else '--' for m in matches],
        score2 = [m[0].score2 if m[0].score2 != None else '--' for m in matches],
        played = [m[0].score1 != None or m[0].score2 != None for m in matches],
    ))

    return render_template(
        'matches/index.html',
        title   = f'Matches of {year}',
        matches = matches_df,
        years   = years,
        year    = year,
    )

@app.route('/about')
def route_about():
    return render_template('about/index.html', title='About')
