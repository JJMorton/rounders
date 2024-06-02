A full-stack web app to manage a summer rounders tournament.

The backend is written in Python using *Flask* and *Jinja2* templating, and the frontend uses a small amount of [htmx](https://htmx.org/).
The database is *SQLite*, and the [SQLAlchemy](https://www.sqlalchemy.org/) Python library is used to interface with it.

## Setup
Requires Python >= **3.11**.
1. Install required packages with `pip install -r requirements.txt`.
2. Create a `.env` file to define needed environment variables in the format `ENV_VAR=...`.
    - `SECRET_KEY` -- generate according to [the flask documentation](https://flask.palletsprojects.com/en/2.3.x/config/#SECRET_KEY)
    - `ADMIN_PASSWORD_HASH` -- generate using `werkzeug.security.generate_password_hash`, docs [here](https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.generate_password_hash)
3. Run with a WSGI server (e.g. gunicorn) or debug with `flask --app rounders:app run --debug`.

## Available endpoints

- `GET` `/`: The homepage
- `GET` `/rules`: Rules of the game


- `GET` `/teams/`: Get a list of all teams
- \*`GET` `/teams/create/`: Get the form to create a team
- \*`GET` `/teams/<int:id>/`: Get a single team
- \*`GET` `/teams/<int:id>/edit`: Get the form to edit a team
- \*`POST` `/teams/`: Create a team
- \*`PATCH` `/teams/<int:id>/`: Edit a team
- \*`DELETE` `/teams/<int:id>/`: Delete a team


- `GET` `/matches/`: Get all matches
- \*`GET` `/matches/create/`: Get the form to create a match
- \*`GET` `/matches/<int:id>/edit/`: Get the form to edit a match
- \*`POST` `/matches/`: Create a match
- \*`PATCH` `/matches/<int:id>/`: Edit a match
- \*`DELETE` `/matches/<int:id>/`: Delete a match


\* *Requires authentication as the administrator*

