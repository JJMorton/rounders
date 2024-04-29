from flask import flash, redirect, request
from flask_login import login_required
from sqlalchemy import or_

from . import app, models, db


@app.route('/createteam', methods=["POST"])
@login_required
def route_createteam():

    redirect_url = request.args.get("next", default=f'/teams', type=str)

    year = request.args.get("year", type=int)
    if not year:
        flash("Invalid year specified")
        return redirect(redirect_url)

    name = request.form.get("name")
    if not name:
        flash("Invalid team name")
        return redirect(redirect_url)

    player_ids = [
        int(id)
        for id in request.form.getlist("players")
    ]

    team = models.Team(name=name, year=year)
    db.session.add(team)
    db.session.commit()

    team_id = team.id
    if not team_id:
        flash("Something went wrong")
        return redirect(redirect_url)

    for player_id in player_ids:
        member = models.Member(player_id=player_id, team_id=team_id)
        db.session.add(member)

    print(db.session.commit())

    flash(f"Created team '{name}'")
    return redirect(redirect_url)


@app.route('/removeteams', methods=["POST"])
@login_required
def route_removeteam():

    redirect_url = request.args.get("next", default=f'/teams', type=str)

    team_ids = [
        int(id)
        for id in request.form.getlist("teams")
    ]

    teams = db.session.scalars(
        db
        .select(models.Team)
        .where(models.Team.id.in_(team_ids))
    ).all()

    members = db.session.scalars(
        db
        .select(models.Member)
        .where(models.Member.team_id.in_(team_ids))
    )

    matches = db.session.scalars(
        db
        .select(models.Match)
        .where(or_(
            models.Match.team1_id.in_(team_ids),
            models.Match.team2_id.in_(team_ids),
        ))
    )

    if not teams:
        flash("No teams removed")
        return redirect(redirect_url)

    for match in matches:
        db.session.delete(match)

    for member in members:
        db.session.delete(member)

    for team in teams:
        db.session.delete(team)

    db.session.commit()

    flash(f"{len(teams)} team(s) removed")
    print(request.args.get("next"))
    return redirect(redirect_url)
