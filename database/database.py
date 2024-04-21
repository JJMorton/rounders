import sqlite3
from os import environ

def create_connection() -> sqlite3.Connection:
    try:
        db_file = environ["ROUNDERS_DB_FILE"]
    except KeyError:
        db_file = "database.db"

    print(f"[database] Opening database {db_file}...")
    con = sqlite3.connect(db_file)

    # Enable foreign key constraints
    con.execute("PRAGMA foreign_keys = ON;")

    return con

def ensure_table(con: sqlite3.Connection):

    cur = con.cursor()

    print("[database] Ensuring tables are created...")
    # Primary keys must also be declared NOT NULL, see:
    # https://stackoverflow.com/questions/64753105/why-can-i-add-null-value-to-primary-key-in-sqlite
    cur.execute("""CREATE TABLE IF NOT EXISTS teams(
        id INTEGER PRIMARY KEY NOT NULL,
        name TEXT NOT NULL,
        year INTEGER NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS players(
        id INTEGER PRIMARY KEY NOT NULL,
        name_first TEXT NOT NULL,
        name_last TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS members(
        player_id INTEGER NOT NULL,
        team_id INTEGER NOT NULL,
        PRIMARY KEY(player_id, team_id),
        FOREIGN KEY(player_id) REFERENCES players(id),
        FOREIGN KEY(team_id) REFERENCES teams(id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS matches(
        id INTEGER PRIMARY KEY NOT NULL,
        team1_id INTEGER NOT NULL,
        team2_id INTEGER NOT NULL,
        score1 REAL NOT NULL,
        score2 REAL NOT NULL,
        play_date INTEGER NOT NULL,
        FOREIGN KEY(team1_id) REFERENCES teams(id),
        FOREIGN KEY(team2_id) REFERENCES teams(id)
    )""")

    tables = cur.execute("SELECT name FROM sqlite_master").fetchall()
    print("[database] Have tables")
    for t, in tables:
        print(f"  - {t}")

CONNECTION = create_connection()
ensure_table(CONNECTION)
