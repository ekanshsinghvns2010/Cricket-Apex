import discord
from discord.ext import commands

from database import connect_db

PLAYERS_PER_EMBED = 25

ROLE_ICONS = {
    "BAT": "🏏",
    "WK": "🧤",
    "AR": "🎯",
    "BOWL": "🎳",
}

COUNTRY_FLAGS = {
    "india": "🇮🇳",
    "england": "🏴",
    "australia": "🇦🇺",
    "pakistan": "🇵🇰",
    "south africa": "🇿🇦",
    "new zealand": "🇳🇿",
    "sri lanka": "🇱🇰",
    "bangladesh": "🇧🇩",
    "west indies": "🏴‍☠️",
    "afghanistan": "🇦🇫",
    "ireland": "🇮🇪",
    "zimbabwe": "🇿🇼",
    "scotland": "🏴",
    "netherlands": "🇳🇱",
    "nepal": "🇳🇵",
    "uae": "🇦🇪",
}


def fetch_all_players():
    """
    Fetches every player from the SQLite players table, sorted by
    OVR descending. Returns a list of sqlite3.Row objects.
    """
    conn = connect_db()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players ORDER BY ovr DESC")
        return cursor.fetchall()
    finally:
        conn.close()


def get_role_icon(role):
    return ROLE_ICONS.get(role, "❔")


def get_country_flag(country):
    if not country:
        return "🌍"
    return COUNTRY_FLAGS.get(country.strip().lower(), "🌍")


def format_player_line(player):
    """
    Formats a single sqlite3.Row into a display line like:
    🏏 Virat Kohli | BAT | 96 OVR | 🇮🇳 India
    """
    icon = get_role_icon(player["role"])
    flag = get_country_flag(player["country"])

    return f"{icon} {player['name']} | {player['role']} | {player['ovr']} OVR | {flag} {player['country']}"


def chunk_players(players, size=PLAYERS_PER_EMBED):
    """Splits a list of players into chunks of at most `size` items."""
    for i in range(0, len(players), size):
        yield players[i:i + size]


def build_embeds(players):
    """
    Builds one or more embeds for the full sorted player list,
    splitting across multiple embeds if there are more than
    PLAYERS_PER_EMBED players.
    """
    total_players = len(players)
    chunks = list(chunk_players(players))
    total_pages = len(chunks)

    embeds = []

    for page_index, chunk in enumerate(chunks, start=1):
        description = "\n".join(format_player_line(p) for p in chunk)

        title = "🏏 All Players"
        if total_pages > 1:
            title += f" (Page {page_index}/{total_pages})"

        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.gold()
        )

        embed.set_footer(text=f"Total Players: {total_players}")

        embeds.append(embed)

    return embeds


def setup_players(bot):

    @bot.command(name="players")
    async def players(ctx):

        all_players = fetch_all_players()

        if not all_players:
            await ctx.send("❌ No players found in the database.")
            return

        embeds = build_embeds(all_players)

        for embed in embeds:
            await ctx.send(embed=embed)
            