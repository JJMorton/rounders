from typing import Optional
from flask import abort, jsonify, request
from . import app, db, config
from .models import Team, Player, Member, Match

@app.route('/api/players/')
def api_players():

    page = db.paginate(
        db.select(Player).order_by(Player.name_last),
        per_page=request.args.get("per_page", default=config.DEFAULT_PAGE_SIZE, type=int),
        max_per_page=config.MAX_PAGE_SIZE,
    )

    if len(page.items) == 0:
        abort(404)

    return jsonify(dict(
        data=[
            dict(id=player.id, name_first=player.name_first, name_last=player.name_last)
            for player in page.items
        ],
        pagination=dict(
            page=page.page,
            per_page=page.per_page,
            prev=page.prev_num,
            next=page.next_num,
        )
    ))

@app.route('/api/teams/')
def api_teams():

    year: Optional[int] = request.args.get("year", type=int)

    page = db.paginate(
        db.select(Team).order_by(Team.name).filter(Team.year == year if year else True),
        per_page=request.args.get("per_page", default=config.DEFAULT_PAGE_SIZE, type=int),
        max_per_page=config.MAX_PAGE_SIZE,
    )

    if len(page.items) == 0:
        abort(404)

    return jsonify(dict(
        data=[
            dict(id=team.id, name=team.name, year=team.year)
            for team in page.items
        ],
        pagination=dict(
            page=page.page,
            per_page=page.per_page,
            prev=page.prev_num,
            next=page.next_num,
        )
    ))
