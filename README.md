A full-stack web app to manage a summer rounders tournament.

## Setup
Requires Python >= **3.11**.
1. Install required packages with `pip install -r requirements.txt`.
2. Create a `.env` file to define needed environment variables in the format `ENV_VAR=...`.
	- `SECRET_KEY` -- generate according to [the flask documentation](https://flask.palletsprojects.com/en/2.3.x/config/#SECRET_KEY)
	- `ADMIN_PASSWORD_HASH` -- generate using `werkzeug.security.generate_password_hash`, docs [here](https://werkzeug.palletsprojects.com/en/3.0.x/utils/#werkzeug.security.generate_password_hash)
3. Run with a WSGI server (e.g. gunicorn) or debug with `flask --app rounders:app run --debug`.
