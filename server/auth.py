from dataclasses import dataclass
import flask
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from os import environ

# Set the secret key on flask
from . import app
app.secret_key = environ.get("SECRET_KEY")


# Initialise the login manager
login = LoginManager(app=app)


# This is very simple, just one admin user
# Create it here using the salted + hashed password
# from environment variables
@dataclass(frozen=True)
class User(UserMixin):
    id: str
    password_hash: str

admin_user = User(
    id='admin',
    password_hash=environ.get("ADMIN_PASSWORD_HASH")
)


# Tell flask-login how to fetch a user, given an id
@login.user_loader
def load_user(user_id):
    return admin_user if user_id == admin_user.get_id() else None


# Define the routes for logging in/out.

# First, the login page that the user is sent
@app.route('/login', methods=['GET'])
def route_login_get():
    return flask.render_template('login/index.html', title="Admin Login")

# Second, the POST method for recieving the login request
@app.route('/login', methods=['POST'])
def route_login_post():
    username = flask.request.form.get('username')
    password = flask.request.form.get('password')
    if (
        username is None
        or password is None
        or (not check_password_hash(admin_user.password_hash, password))
    ):
        flask.flash("Invalid login")
        return flask.redirect("/login")

    flask.flash("Logged in")
    login_user(admin_user, remember=False)
    return flask.redirect('/')

# Route to log out the current user
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flask.flash("Logged out")
    return flask.redirect("/")
