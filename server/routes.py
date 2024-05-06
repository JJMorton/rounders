"""
Defines the endpoints available (i.e. the valid paths that users can make requests to),
and their responses.
"""

from datetime import datetime, timedelta
from dateutil import parser
from flask import flash, redirect, render_template, request
from flask_login import login_required
import pandas as pd
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

from .models import Team, Player, Member, Match
from . import app
from . import config
from . import db


@app.route('/')
def home():

    now = datetime.now()
    today = datetime(year=now.year, month=now.month, day=now.day)
    weekstart = (today - timedelta(days=today.weekday())).timestamp()
    weekend = (today + timedelta(days=7 - today.weekday())).timestamp()
    matches = db.session.scalars(
        db
        .select(Match)
        .filter(and_(Match.play_date >= weekstart, Match.play_date < weekend))
    ).all()

    # Create dataframe, sort by newest first
    matches_df = pd.DataFrame(dict(
        date    = [m.play_date for m in matches],
        id      = [m.id for m in matches],
        name1   = [m.team1.name for m in matches],
        name2   = [m.team2.name for m in matches],
        teamid1 = [m.team1.id for m in matches],
        teamid2 = [m.team2.id for m in matches],
        score1  = [m.score1 if m.score1 != None else '--' for m in matches],
        score2  = [m.score2 if m.score2 != None else '--' for m in matches],
    )).sort_values('date')

    return render_template(
        'home/index.html',
        matches=matches_df,
        title='Home',
    )


@app.route('/teams/')
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

    matches1 = [team.matches1.where(Match.score1 != None).all() for team in teams]
    matches2 = [team.matches2.where(Match.score2 != None).all() for team in teams]

    # # Ignore unplayed matches
    # matches1 = [m for m in matches1 if m.score1 is not None and m.score2 is not None]
    # matches2 = [m for m in matches2 if m.score1 is not None and m.score2 is not None]

    played = [len(m1) + len(m2) for m1, m2 in zip(matches1, matches2)]
    wins = [
        len([m for m in m1 if m.score1 > m.score2])
        + len([m for m in m2 if m.score2 > m.score1])
        for m1, m2 in zip(matches1, matches2)
    ]
    losses = [
        len([m for m in m1 if m.score1 < m.score2])
        + len([m for m in m2 if m.score2 < m.score1])
        for m1, m2 in zip(matches1, matches2)
    ]
    draws = [p - w - l for p, w, l in zip(played, wins, losses)]
    points = [2 * w + d for w, d in zip(wins, draws)]

    # Create table of teams, total scores and play count, sorting by score
    teams_df = pd.DataFrame(dict(
        id          = [t.id for t in teams],
        name        = [t.name for t in teams],
        match_count = played,
        points      = points,
        wins        = wins,
        draws       = draws,
        losses      = losses,
    )).sort_values('points', ascending=False)

    return render_template(
        'teams/index.html',
        title = f'Standings of {year}',
        teams = teams_df,
        year  = year,
        years = years,
    )


@app.route('/teams/<int:id>/')
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
        q1.c.id,
        q1.c.play_date,
        q1.c.score1,
        q1.c.score2
    ).join(Team, Team.id == q1.c.team2_id)

    # Get (score2, score1) from matches where this was team2
    q2 = team.matches2.subquery()
    select2 = db.select(
        Team.id,
        Team.name,
        q2.c.id,
        q2.c.play_date,
        q2.c.score2,
        q2.c.score1
    ).join(Team, Team.id == q2.c.team1_id)

    matches = (
        list(db.session.execute(select1).fetchall())
        + list(db.session.execute(select2).fetchall())
    )

    # Sort by date, put unscheduled matches at the top (newest)
    matches_df = pd.DataFrame(dict(
        date    = [m.play_date for m in matches],
        id      = [m[2] for m in matches],
        name1   = [team.name] * len(matches),
        name2   = [m.name for m in matches],
        teamid1 = [team.id] * len(matches),
        teamid2 = [m[0] for m in matches],
        score1  = [m[4] if m[4] != None else '--' for m in matches],
        score2  = [m[5] if m[5] != None else '--' for m in matches],
        played  = [m[4] != None or m[5] != None for m in matches],
    )).sort_values('date', ascending=False)

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


@app.route('/teams/create', methods=["GET"])
@login_required
def route_create_team():

    # Get a list of available years
    years = sorted(db.session.execute(db.select(Team.year).distinct()).scalars().all())
    if not years: years.append(datetime.now().year)

    # Use the year specified in the query parameters,
    # otherwise use the latest available year
    year: int = request.args.get('year', default=years[-1], type=int)

    # Fetch the players
    players = db.session.scalars(
        db
        .select(Player)
        .order_by(Player.name_last)
    ).all()

    # Create table of teams for the form options
    players_df = pd.DataFrame(dict(
        id         = [p.id for p in players],
        name_first = [p.name_first for p in players],
        name_last = [p.name_last for p in players],
    )).sort_values('name_last')

    return render_template(
        'teams/create.html',
        title   = f"New Team ({year})",
        players = players_df,
        year    = year,
        next    = request.args.get('next', default='/teams/create')
    )


@app.route('/teams/create', methods=["POST"])
@login_required
def route_create_team_post():

    redirect_url = request.args.get("next", default=f'/teams', type=str)

    year = request.form.get("year", type=int)
    if not year:
        flash("Invalid year specified")
        return redirect(redirect_url)

    name = request.form.get("name")
    # Very basic sanitisation, just to prevent mistakes.
    # Doesn't need to be elaborate, as long as I'm aware of where
    # the name is being used.
    forbid_chars = ['\\', '\'', '"', ';', '<', '>']
    if name: name = ''.join(ch for ch in name if not ch in forbid_chars)
    if not name:
        flash("Invalid team name")
        return redirect(redirect_url)

    player_ids = [
        int(id)
        for id in request.form.getlist("players")
    ]

    team = Team(name=name, year=year)
    db.session.add(team)
    db.session.commit()

    team_id = team.id
    if not team_id:
        flash("Something went wrong")
        return redirect(redirect_url)

    for player_id in player_ids:
        member = Member(player_id=player_id, team_id=team_id)
        db.session.add(member)

    db.session.commit()

    flash(f"Created team '{name}'")
    return redirect(redirect_url)


@app.route('/teams/<int:id>/edit', methods=["GET"])
@login_required
def route_edit_team(id):

    team = db.get_or_404(Team, int(id))

    # Fetch the players
    players = db.session.scalars(
        db
        .select(Player)
        .order_by(Player.name_last)
    ).all()

    # Create table of teams for the form options
    players_df = pd.DataFrame(dict(
        id         = [p.id for p in players],
        name_first = [p.name_first for p in players],
        name_last = [p.name_last for p in players],
    )).sort_values('name_last')

    return render_template(
        'teams/edit.html',
        title      = f'Edit Team "{team.name}"',
        id         = team.id,
        name       = team.name,
        member_ids = [m.player_id for m in team.members],
        players    = players_df,
        next       = request.args.get('next', default='/teams/create')
    )


@app.route('/teams/<int:id>/edit', methods=["POST"])
@login_required
def route_edit_team_post(id):

    team = db.get_or_404(Team, int(id))

    redirect_url = request.args.get("next", default=f'/teams?year={team.year}', type=str)

    player_ids = [
        int(id)
        for id in request.form.getlist("players")
    ]

    members = db.session.scalars(
        db
        .select(Member)
        .where(Member.team_id == team.id)
    )

    for member in members:
        db.session.delete(member)
    db.session.commit()

    for id in player_ids:
        member = Member(player_id=id, team_id=team.id)
        db.session.add(member)
    db.session.commit()

    flash(f"Updated team '{team.name}'")
    return redirect(redirect_url)


@app.route('/teams/<int:id>/remove', methods=["POST"])
@login_required
def route_remove_team_post(id):

    redirect_url = request.args.get("next", default=f'/teams', type=str)

    team = db.session.scalars(
        db
        .select(Team)
        .where(Team.id == id)
    ).first()

    if not team:
        flash("Attempted to remove non-existent team")
        return redirect(redirect_url)

    team_name = team.name

    members = db.session.scalars(
        db
        .select(Member)
        .where(Member.team_id == team.id)
    )

    matches = db.session.scalars(
        db
        .select(Match)
        .where(or_(
            Match.team1_id == id,
            Match.team2_id == id,
        ))
    )

    for match in matches:
        db.session.delete(match)

    for member in members:
        db.session.delete(member)

    db.session.delete(team)
    db.session.commit()

    flash(f"Removed team '{team_name}'")
    return redirect(redirect_url)


@app.route('/matches/')
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

    # Create dataframe, sort by newest first
    matches_df = pd.DataFrame(dict(
        date    = [m[0].play_date for m in matches],
        id      = [m[0].id for m in matches],
        name1   = [m[1].name for m in matches],
        name2   = [m[2].name for m in matches],
        teamid1 = [m[1].id for m in matches],
        teamid2 = [m[2].id for m in matches],
        score1  = [m[0].score1 if m[0].score1 != None else '--' for m in matches],
        score2  = [m[0].score2 if m[0].score2 != None else '--' for m in matches],
        played  = [m[0].score1 != None or m[0].score2 != None for m in matches],
    )).sort_values('date', ascending=False)

    return render_template(
        'matches/index.html',
        title   = f'Matches of {year}',
        matches = matches_df,
        years   = years,
        year    = year,
    )


@login_required
@app.route('/matches/create', methods=["GET"])
def route_create_match():

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

    # Create table of teams for the form options
    teams_df = pd.DataFrame(dict(
        id          = [t.id for t in teams],
        name        = [t.name for t in teams],
    )).sort_values('name')

    return render_template(
        'matches/create.html',
        title = f"New Match ({year})",
        teams = teams_df,
        year  = year,
        next  = request.args.get('next', default='/matches/create')
    )


@app.route('/matches/create', methods=["POST"])
@login_required
def route_create_match_post():

    redirect_url = request.args.get("next", default=f'/matches/create', type=str)

    team1_id = request.form.get("team1")
    team2_id = request.form.get("team2")
    if not team1_id or not team2_id:
        flash("Invalid team")
        return redirect(redirect_url)

    team1 = db.session.scalar(
        db.select(Team).where(Team.id == team1_id)
    )
    team2 = db.session.scalar(
        db.select(Team).where(Team.id == team2_id)
    )
    if not team1 or not team2:
        flash("Invalid team")
        return redirect(redirect_url)

    date_str = request.form.get("date")
    time_str = request.form.get("time") or "00:00"
    date = parser.parse(f'{date_str}T{time_str}:00Z').timestamp() if date_str else None

    score1 = request.form.get("score1", default=None, type=float)
    score2 = request.form.get("score2", default=None, type=float)

    # If one team is awarded points, the other should get 0
    if score1 != None or score2 != None:
        if score1 == None: score1 = 0
        if score2 == None: score2 = 0

    match = Match(
        team1_id=team1_id,
        team2_id=team2_id,
        score1=score1,
        score2=score2,
        play_date=date
    )

    db.session.add(match)
    db.session.commit()

    if not match.id:
        flash("Something went wrong")
        return redirect(redirect_url)

    flash("Created match")
    return redirect(redirect_url)


@login_required
@app.route('/matches/<int:id>/edit', methods=["GET"])
def route_edit_match(id):

    match = db.get_or_404(Match, int(id))

    return render_template(
        'matches/edit.html',
        title     = "Edit Match",
        id        = match.id,
        team1     = match.team1.name,
        team2     = match.team2.name,
        timestamp = match.play_date,
        score1    = match.score1,
        score2    = match.score2,
        year      = match.team1.year,
        next      = request.args.get('next', default='/matches/create')
    )


@app.route('/matches/<int:id>/edit', methods=["POST"])
@login_required
def route_edit_match_post(id):

    redirect_url = request.args.get("next", default=f'/matches', type=str)

    match = db.get_or_404(Match, int(id))

    date_str = request.form.get("date")
    time_str = request.form.get("time") or "00:00"
    date = parser.parse(f'{date_str}T{time_str}:00Z').timestamp() if date_str else None

    score1 = request.form.get("score1", default=None, type=float)
    score2 = request.form.get("score2", default=None, type=float)

    # If one team is awarded points, the other should get 0
    if score1 != None or score2 != None:
        if score1 == None: score1 = 0
        if score2 == None: score2 = 0

    match.play_date = date
    match.score1 = score1
    match.score2 = score2
    db.session.commit()

    flash("Updated match")
    return redirect(redirect_url)


@app.route('/matches/<int:id>/remove', methods=["POST"])
@login_required
def route_remove_match_post(id):

    redirect_url = request.args.get("next", default=f'/matches', type=str)

    match = db.session.scalar(
        db
        .select(Match)
        .where(Match.id == id)
    )

    if not match:
        flash("Attempted to remove non-existent match")
        return redirect(redirect_url)

    db.session.delete(match)
    db.session.commit()

    flash(f"Removed match")
    return redirect(redirect_url)
