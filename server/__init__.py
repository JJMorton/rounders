"""
The Flask server and SQLite database
"""

from pathlib import Path
import config

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from sqlalchemy.engine import Engine


# --------------------------------------------
# Create flask server

app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='')
# Limit content upload size to 20MB
app.config['MAX_CONTENT_LENGTH'] = 20 * 1000 * 1000
# Create attachments folder for blogs
app.config['ATTACHMENTS_FOLDER'] = Path(app.root_path, 'static/attachments')
app.config['ATTACHMENTS_FOLDER'].mkdir(parents=True, exist_ok=True)


# --------------------------------------------
# Set up the database

class ModelBase(DeclarativeBase):
    """Base class for models"""
    pass

# Initialise database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{config.DATABASE_FILE}"
db = SQLAlchemy(app=app, model_class=ModelBase)

# Enable foreign key checks when connecting
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


# --------------------------------------------
# Import submodules

from . import models
from . import blogs
from . import routes
from . import auth
