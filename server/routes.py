"""
Defines the endpoints available (i.e. the valid paths that users can make requests to),
and their responses.
"""

from datetime import datetime
from flask import render_template, request

from . import models
from . import app
from . import config
from . import db

@app.route('/')
def home():
    return render_template('home/index.html', title='Home')

@app.route('/teams')
def teams():
    # Get a list of all teams

    # Get a list of available years
    years = sorted(db.session.execute(db.select(models.Team.year).distinct()).scalars().all())
    if not years: years.append(datetime.now().year)

    # Decide which year to show
    year: int = request.args.get('year', default=years[-1], type=int)

    # Fetch the teams
    teams = db.session.scalars(
        db
        .select(models.Team)
        .where(models.Team.year == year)
        .order_by(models.Team.id)
    ).all()

    # Count number of matches
    match_counts = [
        len(team.matches1.all()) + len(team.matches2.all())
        for team in teams
    ]

    # Compute the total scores
    scores = [
        sum(m.score1 for m in team.matches1.all()) + sum(m.score2 for m in team.matches2.all())
        for team in teams
    ]

    # Zip together the teams and total scores, sorting by score
    table_data = sorted(zip(teams, scores, match_counts), key=lambda x: x[1], reverse=True)

    return render_template(
        'teams/index.html',
        title=f'Teams of {year}',
        table_data=table_data,
        year=year,
        years=years,
    )

@app.route('/teams/<int:id>')
def team(id: int):
    team = db.get_or_404(models.Team, int(id))

    # Get (score1, score2) from matches where this was team1
    q1 = team.matches1.subquery()
    query = db.select(models.Team, q1.c.score1, q1.c.score2).join(models.Team, models.Team.id == q1.c.team2_id)
    matches1 = db.session.execute(query).fetchall()

    # Get (score2, score1) from matches where this was team2
    q2 = team.matches2.subquery()
    query = db.select(models.Team, q2.c.score2, q2.c.score1).join(models.Team, models.Team.id == q2.c.team1_id)
    matches2 = db.session.execute(query).fetchall()

    table_data = [
        (team, other_team, this_score, other_score)
        for other_team, this_score, other_score in (matches1 + matches2)
    ]

    return render_template(
        'teams/team.html',
        title=f'Team "{team.name}"',
        team=team,
        table_data=table_data
    )

@app.route('/about')
def about():
    return render_template('about/index.html', title='About')

