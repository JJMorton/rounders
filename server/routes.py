"""
Defines the endpoints available (i.e. the valid paths that users can make requests to),
and their responses.
"""

from datetime import datetime
from flask import render_template, request
import pandas as pd

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

    # Create table of teams, total scores and play count, sorting by score
    df = pd.DataFrame(dict(
        id = [t.id for t in teams],
        name = [t.name for t in teams],
        match_count = [
            len(team.matches1.all()) + len(team.matches2.all())
            for team in teams
        ],
        score = [
            sum(m.score1 for m in team.matches1.all()) + sum(m.score2 for m in team.matches2.all())
            for team in teams
        ]
    )).sort_values('score')

    return render_template(
        'teams/index.html',
        title=f'Teams of {year}',
        table=df,
        year=year,
        years=years,
    )

@app.route('/teams/<int:id>')
def team(id: int):
    team = db.get_or_404(models.Team, int(id))

    # Get (score1, score2) from matches where this was team1
    q1 = team.matches1.subquery()
    select1 = db.select(
        models.Team.id,
        models.Team.name,
        q1.c.play_date,
        q1.c.score1,
        q1.c.score2
    ).join(models.Team, models.Team.id == q1.c.team2_id)

    # Get (score2, score1) from matches where this was team2
    q2 = team.matches2.subquery()
    select2 = db.select(
        models.Team.id,
        models.Team.name,
        q2.c.play_date,
        q2.c.score1,
        q2.c.score2
    ).join(models.Team, models.Team.id == q2.c.team1_id)

    matches =\
        list(db.session.execute(select1).fetchall())\
        + list(db.session.execute(select2).fetchall())

    matches_df = pd.DataFrame(dict(
        date = [datetime.fromtimestamp(m.play_date).strftime('%d %b') for m in matches],
        name1 = [team.name] * len(matches),
        name2 = [m.name for m in matches],
        id1 = [team.id] * len(matches),
        id2 = [m.id for m in matches],
        score1 = [m.score1 for m in matches],
        score2 = [m.score2 for m in matches],
    ))

    return render_template(
        'teams/team.html',
        title=f'Team "{team.name}"',
        team=team,
        matches=matches_df,
    )

@app.route('/about')
def about():
    return render_template('about/index.html', title='About')

