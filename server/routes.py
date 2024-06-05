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
from time import perf_counter

from .models import Team, Player, Match
from . import app
from . import db
from . import formatting as fmt


class Timer:
    start_time: float

    def __init__(self):
        self.start_time = perf_counter()

    @property
    def elapsed_ms(self) -> float:
        return perf_counter() - self.start_time


@app.route('/')
def home():
    timer = Timer()

    now = datetime.now()
    today = datetime(year=now.year, month=now.month, day=now.day)
    weekday_start_sat = (today.weekday() + 2) % 7
    weekstart = (today - timedelta(days=weekday_start_sat)).timestamp()
    weekend = (today + timedelta(days=7 - weekday_start_sat)).timestamp()
    matches = db.session.scalars(
        db
        .select(Match)
        .filter(and_(Match.play_date >= weekstart, Match.play_date < weekend))
    ).all()

    matches_df = pd.DataFrame(dict(
        date    = [fmt.AsDate(m.play_date, newest_first=False) for m in matches],
        time    = [fmt.AsTime(m.play_date, newest_first=False) for m in matches],
        id      = [m.id for m in matches],
        name1   = [fmt.AsTeamName(m.team1) for m in matches],
        name2   = [fmt.AsTeamName(m.team2) for m in matches],
        teamid1 = [m.team1.id for m in matches],
        teamid2 = [m.team2.id for m in matches],
        score1  = [fmt.AsScore(m.score1) for m in matches],
        score2  = [fmt.AsScore(m.score2) for m in matches],
        played  = [m.played for m in matches],
    )).sort_values('date')

    return render_template(
        'home/index.html',
        matches=matches_df,
        title='Home',
        millis=timer.elapsed_ms
    )


@app.route('/teams/')
def route_teams():
    """Get a list of all teams"""

    timer = Timer()

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

    # Fetch all matches played by each team
    matches = [
        [
            match for match in db.session.scalars(
                db.select(Match).where(or_(Match.team1_id == team.id, Match.team2_id == team.id))
            ).all()
            if match.played
        ]
        for team in teams
    ]

    # Compute no. of plays, wins, losses, etc.
    played = [len(m) for m in matches]
    wins = [
        len([m for m in ms if m.winner and m.winner.id == team.id])
        for ms, team in zip(matches, teams)
    ]
    draws = [
        len([m for m in ms if m.winner is None])
        for ms in matches
    ]
    losses = [p - w - d for p, w, d in zip(played, wins, draws)]
    points = [2 * w + d for w, d in zip(wins, draws)]

    # Total number of rounders scored and conceded
    scored = [
        sum(m.pov_score(team).home or 0 for m in ms)
        for ms, team in zip(matches, teams)
    ]
    conceded = [
        sum(m.pov_score(team).away or 0 for m in ms)
        for ms, team in zip(matches, teams)
    ]

    # Create table of teams, total scores and play count, sorting by score
    teams_df = pd.DataFrame(dict(
        id          = [t.id for t in teams],
        name        = [fmt.AsTeamName(t) for t in teams],
        match_count = played,
        points      = points,
        wins        = wins,
        draws       = draws,
        losses      = losses,
        scored      = [ fmt.AsScore(s / p if p else 0) for s, p in zip(scored, played) ],
        conceded    = [ fmt.AsScore(c / p if p else 0) for c, p in zip(conceded, played) ],
        difference  = [ fmt.AsScore((s - c) / p if p else 0) for s, c, p in zip(scored, conceded, played) ],
    )).sort_values('difference', ascending=False).sort_values('points', ascending=False)

    sortby = request.args.get('sortby')
    if sortby in teams_df:
        teams_df = teams_df.sort_values(sortby, ascending=sortby=='name')

    # Render only the table if the request is from htmx
    template = 'teams/table.html' if request.headers.get('hx-request') else 'teams/index.html'

    return render_template(
        template,
        title    = f'Team Standings',
        teams    = teams_df,
        year     = year,
        detailed = 'detailed' in request.args,
        years    = years,
        millis   = timer.elapsed_ms,
    )


@app.route('/teams/', methods=["POST"])
@login_required
def route_teams_post():
    """Create a team"""

    redirect_url = request.args.get("next", default=f'/teams', type=str)

    year = request.form.get("year", type=int)
    if not year:
        flash("Invalid year specified")
        return redirect(redirect_url)

    name = request.form.get("name")
    # Very basic sanitisation, just to prevent mistakes.
    # Doesn't need to be elaborate, as long as I'm aware of where
    # the name is being used.
    if name:
        name = fmt.basic_sanitisation(name)
    else:
        flash("Invalid team name")
        return redirect(redirect_url)

    team = Team(name=name, year=year) # type: ignore
    db.session.add(team)
    db.session.commit()

    team_id = team.id
    if not team_id:
        flash("Something went wrong")
        return redirect(redirect_url)

    # Find corresponding existing players, or create new ones
    first_names = request.form.getlist("name-first")
    last_names = request.form.getlist("name-last")
    players = [
        Player(
            team_id=team_id,
            name_first=fmt.basic_sanitisation(first),
            name_last=fmt.basic_sanitisation(last),
        ) # type: ignore
        for first, last in zip(first_names, last_names)
    ]

    for player in players:
        db.session.add(player)
    db.session.commit()

    if not all(player.id for player in players):
        flash("Something went wrong")
        return redirect(redirect_url)

    flash(f"Created team '{name}'")
    return redirect(redirect_url)


@app.route('/teams/create/', methods=["GET"])
@login_required
def route_teams_postform():
    """Get the form to create a team"""

    timer = Timer()

    # Get a list of available years
    years = sorted(db.session.execute(db.select(Team.year).distinct()).scalars().all())
    if not years: years.append(datetime.now().year)

    # Use the year specified in the query parameters,
    # otherwise use the latest available year
    year: int = request.args.get('year', default=years[-1], type=int)

    return render_template(
        'teams/create.html',
        title   = f"New Team ({year})",
        year    = year,
        next    = request.args.get('next', default=f'/teams?year={year}'),
        millis  = timer.elapsed_ms,
    )


@app.route('/teams/<int:id>/')
def route_team(id: int):
    """Get a single team"""

    timer = Timer()

    team = db.get_or_404(Team, int(id))

    matches: list[Match] = db.session.scalars(
        db.select(Match).where(or_(Match.team1_id == team.id, Match.team2_id == team.id))
    ).all() # type: ignore

    matches_df = pd.DataFrame(dict(
        date    = [fmt.AsDate(m.play_date) for m in matches],
        id      = [m.id for m in matches],
        name1   = [fmt.AsTeamName(team)] * len(matches),
        name2   = [fmt.AsTeamName(m.opponent_of(team)) for m in matches],
        teamid1 = [team.id] * len(matches),
        teamid2 = [m.opponent_of(team).id for m in matches],
        score1  = [fmt.AsScore(m.pov_score(team).home) for m in matches],
        score2  = [fmt.AsScore(m.pov_score(team).away) for m in matches],
        played  = [m.played for m in matches],
    )).sort_values('date')

    players_df = pd.DataFrame(dict(
        name_first = [p.name_first for p in team.players],
        name_last  = [p.name_last for p in team.players],
    ))

    return render_template(
        'teams/team.html',
        title   = f'Team "{team.name}"',
        team    = team,
        matches = matches_df,
        players = players_df,
        millis=timer.elapsed_ms,
    )


@app.route('/teams/<int:id>/edit/', methods=["POST"])
@login_required
def route_team_patch(id):
    """Edit a team"""

    team = db.get_or_404(Team, int(id))
    redirect_url = request.args.get("next", default=f'/teams?year={team.year}', type=str)

    # Delete and re-create all players
    for player in team.players:
        db.session.delete(player)

    first_names = request.form.getlist("name-first")
    last_names = request.form.getlist("name-last")
    players = [
        Player(
            team_id=team.id,
            name_first=fmt.basic_sanitisation(first),
            name_last=fmt.basic_sanitisation(last),
        ) # type: ignore
        for first, last in zip(first_names, last_names)
    ]

    for player in players:
        db.session.add(player)
    db.session.commit()

    if not all(player.id != None for player in players):
        flash("Something went wrong")
        return redirect(redirect_url)

    flash(f"Updated team '{team.name}'")
    return redirect(redirect_url)


@app.route('/teams/<int:id>/edit', methods=["GET"])
@login_required
def route_team_patchform(id):
    """Get the form to edit a team"""

    timer = Timer()

    team = db.get_or_404(Team, int(id))

    # Create table of teams for the form options
    players_df = pd.DataFrame(dict(
        id         = [p.id for p in team.players],
        name_first = [p.name_first for p in team.players],
        name_last = [p.name_last for p in team.players],
    )).sort_values('name_last')
 
    return render_template(
        'teams/edit.html',
        title      = f'Edit Team "{team.name}"',
        id         = team.id,
        name       = fmt.AsTeamName(team),
        players    = players_df,
        next       = request.args.get('next', default=f'/teams/{id}', type=str),
        millis     = timer.elapsed_ms,
    )


@app.route('/teams/<int:id>/delete/', methods=["POST"])
@login_required
def route_team_delete(id):
    """Delete a team"""

    team = db.get_or_404(Team, int(id))
    redirect_url = request.args.get("next", default=f'/teams', type=str)

    team_name = team.name

    players = db.session.scalars(
        db
        .select(Player)
        .where(Player.team_id == team.id)
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

    for player in players:
        db.session.delete(player)

    db.session.delete(team)
    db.session.commit()

    flash(f"Removed team '{team_name}'")
    return redirect(redirect_url)


@app.route('/matches/')
def route_matches():
    """Get all matches"""

    timer = Timer()

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
        week    = [fmt.AsWeekOf(m[0].play_date, newest_first=m[0].played) for m in matches],
        date    = [fmt.AsDate(m[0].play_date, newest_first=m[0].played) for m in matches],
        time    = [fmt.AsTime(m[0].play_date, newest_first=m[0].played) for m in matches],
        id      = [m[0].id for m in matches],
        name1   = [fmt.AsTeamName(m[1]) for m in matches],
        name2   = [fmt.AsTeamName(m[2]) for m in matches],
        teamid1 = [m[1].id for m in matches],
        teamid2 = [m[2].id for m in matches],
        score1  = [fmt.AsScore(m[0].score1) for m in matches],
        score2  = [fmt.AsScore(m[0].score2) for m in matches],
        played  = [m[0].played for m in matches],
    )).sort_values('date')

    groupby = request.args.get('groupby')
    if not groupby in matches_df:
        groupby = 'week'

    # Render only the list if the request is from htmx
    template = 'matches/list_grouped.html' if request.headers.get('hx-request') else 'matches/index.html'

    return render_template(
        template,
        title   = f'Matches',
        matches = matches_df,
        groupby = groupby,
        years   = years,
        year    = year,
        millis  = timer.elapsed_ms,
    )


@app.route('/matches/', methods=["POST"])
@login_required
def route_matches_post():
    """Create a match"""

    redirect_url = request.args.get('next', default=f'/matches/create', type=str)

    team1_id = request.form.get("team1", type=int)
    team2_id = request.form.get("team2", type=int)
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
    date = int(parser.parse(f'{date_str}T{time_str}:00Z').timestamp()) if date_str else None

    innings1 = (
        request.form.get("score1_in1", default=None, type=float),
        request.form.get("score1_in2", default=None, type=float),
    )
    innings2 = (
        request.form.get("score2_in1", default=None, type=float),
        request.form.get("score2_in2", default=None, type=float),
    )

    match = Match(
        team1_id=team1_id,
        team2_id=team2_id,
        score1=Match.score_from_innings(*innings1),
        score2=Match.score_from_innings(*innings2),
        score1_in1=innings1[0],
        score2_in1=innings2[0],
        play_date=date
    ) # type: ignore

    db.session.add(match)
    db.session.commit()

    if not match.id:
        flash("Something went wrong")
        return redirect(redirect_url)

    flash("Created match")
    return redirect(redirect_url)



@app.route('/matches/create/', methods=["GET"])
@login_required
def route_matches_postform():
    """Get the form to create a match"""

    timer = Timer()

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
        name        = [fmt.AsTeamName(t) for t in teams],
    )).sort_values('name')

    return render_template(
        'matches/create.html',
        title = f"New Match ({year})",
        teams = teams_df,
        year  = year,
        next  = request.args.get('next', default='/matches/create'),
        millis=timer.elapsed_ms,
    )


@app.route('/matches/<int:id>/edit', methods=["POST"])
@login_required
def route_match_patch(id):
    """Edit a match"""

    redirect_url = request.args.get("next", default=f'/matches', type=str)

    match = db.get_or_404(Match, int(id))

    date_str = request.form.get("date")
    time_str = request.form.get("time") or "00:00"
    date = int(parser.parse(f'{date_str}T{time_str}:00Z').timestamp()) if date_str else None

    innings1 = (
        request.form.get("score1_in1", default=None, type=float),
        request.form.get("score1_in2", default=None, type=float),
    )
    innings2 = (
        request.form.get("score2_in1", default=None, type=float),
        request.form.get("score2_in2", default=None, type=float),
    )

    match.play_date = date
    match.score1 = Match.score_from_innings(*innings1)
    match.score2 = Match.score_from_innings(*innings2)
    match.score1_in1 = innings1[0]
    match.score2_in1 = innings2[0]
    db.session.commit()

    flash("Updated match")
    return redirect(redirect_url)

@login_required
@app.route('/matches/<int:id>/edit/', methods=["GET"])
def route_match_patchform(id):
    """Get the form to edit a match"""

    timer = Timer()

    match = db.get_or_404(Match, int(id))

    return render_template(
        'matches/edit.html',
        title      = "Edit Match",
        id         = match.id,
        team1      = fmt.AsTeamName(match.team1),
        team2      = fmt.AsTeamName(match.team2),
        date       = fmt.AsDateInput(match.play_date),
        time       = fmt.AsTimeInput(match.play_date),
        # FIXME: For matches where the innings were not recorded
        # separately, put the total score in inning 1.
        score1_in1 = match.score1_in1 or match.score1,
        score1_in2 = match.score1_in2,
        score2_in1 = match.score2_in1 or match.score2,
        score2_in2 = match.score2_in2,
        year       = match.team1.year,
        next       = request.args.get('next', default='/matches/create'),
        millis     = timer.elapsed_ms,
    )


@app.route('/matches/<int:id>/delete/', methods=["POST"])
@login_required
def route_match_delete(id):
    """Delete a match"""

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


@app.route('/rules')
def route_rules():
    return render_template('rules/index.html', title="Rules")