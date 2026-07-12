"""
database.py

Handles SQLite database connectivity and schema setup for the
Discord cricket card bot.

Database file: cricket_go.db
"""

import sqlite3

DB_NAME = "cricket_go.db"


def connect_db():
    """
    Opens and returns a new connection to the SQLite database.

    The connection's row_factory is set to sqlite3.Row so query
    results can be accessed both by column name and by index.

    Returns:
        sqlite3.Connection: An open database connection.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """
    Creates all required tables if they do not already exist.

    Currently creates:
        - players: stores all player card data used by the bot.

    The connection is always closed after the operation completes,
    even if an error occurs.
    """
    conn = connect_db()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id TEXT PRIMARY KEY,
                name TEXT,
                display_name TEXT,
                country TEXT,
                team TEXT,
                role TEXT,
                batting_style TEXT,
                bowling_style TEXT,
                ovr INTEGER,
                batting_ovr INTEGER,
                bowling_ovr INTEGER,
                fielding_ovr INTEGER,
                fitness INTEGER,
                rarity TEXT,
                matches INTEGER DEFAULT 0,
                runs INTEGER DEFAULT 0,
                wickets INTEGER DEFAULT 0,
                catches INTEGER DEFAULT 0,
                price INTEGER,
                sell_price INTEGER,
                image TEXT
            )
        """)
        cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        coins INTEGER DEFAULT 500,
        gems INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0,
        losses INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        trophies INTEGER DEFAULT 0,
        matches_played INTEGER DEFAULT 0,
        role TEXT,
        team TEXT,
        batting INTEGER DEFAULT 40,
        bowling INTEGER DEFAULT 40,
        fitness INTEGER DEFAULT 40,
        experience INTEGER DEFAULT 40,
        lifetime_earned INTEGER DEFAULT 0,
        lifetime_spent INTEGER DEFAULT 0
    )
""")
        conn.commit()

    finally:
        conn.close()


# Ensure the schema exists as soon as this module is imported.
create_tables()
