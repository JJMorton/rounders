"""
Defines the endpoints available (i.e. the valid paths that users can make requests to),
and their responses.
"""

from datetime import datetime
from flask import render_template, request

from . import models
from . import app
from . import api
from . import db

@app.route('/')
def home():
    return render_template('home/index.html', title='Home')

@app.route('/teams')
def teams():
    year: int = request.args.get('year', default=datetime.now().year, type=int)
    teams = api.teams(year)
    years = db.session.execute(db.select(models.Team.year).distinct()).scalars().all()
    print(years)
    return render_template(
        'teams/index.html',
        title=f'Teams of {year}',
        pagination=teams,
        years=years,
    )

@app.route('/teams/<int:id>')
def team(id: int):
    team = api.team(id)
    return render_template('teams/team.html', title=f'Team "{team.name}"', team=team)

@app.route('/about')
def about():
    return render_template('about/index.html', title='About')

