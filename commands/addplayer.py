import discord
from discord.ext import commands
import sqlite3
import uuid
import asyncio

from database import connect_db
from utils.logger import log_action
OWNER_ID = 1451236422785958040

FIELD_LABELS = [
    "Player Name",
    "Country",
    "Team",
    "Role",
    "Batting Style",
    "Bowling Style",
    "OVR",
    "Batting OVR",
    "Bowling OVR",
    "Fielding OVR",
    "Fitness",
    "Rarity",
    "Price",
    "Sell Price",
    "Image URL",
]

NUMERIC_STAT_FIELDS = [
    "OVR",
    "Batting OVR",
    "Bowling OVR",
    "Fielding OVR",
    "Fitness",
]

NUMERIC_ECONOMY_FIELDS = [
    "Price",
    "Sell Price",
]

VALID_ROLES = ["BAT", "BOWL", "AR", "WK"]
VALID_RARITIES = ["Common", "Rare", "Epic", "Legendary", "Icon"]

INPUT_TIMEOUT_SECONDS = 180
CONFIRM_TIMEOUT_SECONDS = 60


def parse_player_input(content):
    """
    Parses and validates the raw multi-line message content submitted
    by the owner into a ready-to-insert player dict.

    Args:
        content (str): The raw message content.

    Returns:
        (dict | None, str | None): (player_dict, None) on success, or
        (None, error_message) if validation failed.
    """
    lines = [line.strip() for line in content.strip().splitlines()]
    lines = [line for line in lines if line != ""]

    if len(lines) != 15:
        return None, (
            f"❌ Expected exactly 15 lines, but received {len(lines)}. "
            "Please run `g!addplayer` again and follow the format exactly."
        )

    raw = dict(zip(FIELD_LABELS, lines))

    # Validate and convert numeric stat fields (0-99)
    numeric_values = {}

    for field in NUMERIC_STAT_FIELDS:
        raw_value = raw[field]
        try:
            value = int(raw_value)
        except ValueError:
            return None, f"❌ '{field}' must be a whole number. You entered: `{raw_value}`"

        if not (0 <= value <= 99):
            return None, f"❌ '{field}' must be between 0 and 99. You entered: `{value}`"

        numeric_values[field] = value

    # Validate and convert economy fields (>= 0)
    for field in NUMERIC_ECONOMY_FIELDS:
        raw_value = raw[field]
        try:
            value = int(raw_value)
        except ValueError:
            return None, f"❌ '{field}' must be a whole number. You entered: `{raw_value}`"

        if value < 0:
            return None, f"❌ '{field}' must be 0 or greater. You entered: `{value}`"

        numeric_values[field] = value

    # Validate role
    role = raw["Role"].strip().upper()
    if role not in VALID_ROLES:
        return None, (
            f"❌ Invalid Role: `{raw['Role']}`. "
            f"Must be one of: {', '.join(VALID_ROLES)}"
        )

    # Validate rarity (case-insensitive match against the allowed list)
    rarity_input = raw["Rarity"].strip()
    rarity_lookup = {r.lower(): r for r in VALID_RARITIES}
    rarity_key = rarity_input.lower()

    if rarity_key not in rarity_lookup:
        return None, (
            f"❌ Invalid Rarity: `{raw['Rarity']}`. "
            f"Must be one of: {', '.join(VALID_RARITIES)}"
        )

    rarity = rarity_lookup[rarity_key]

    name = raw["Player Name"].strip()

    if not name:
        return None, "❌ Player Name must not be empty."

    player = {
        "id": str(uuid.uuid4()),
        "name": name,
        "display_name": name.upper(),
        "country": raw["Country"].strip().title(),
        "team": raw["Team"].strip().upper(),
        "role": role,
        "batting_style": raw["Batting Style"].strip(),
        "bowling_style": raw["Bowling Style"].strip(),
        "ovr": numeric_values["OVR"],
        "batting_ovr": numeric_values["Batting OVR"],
        "bowling_ovr": numeric_values["Bowling OVR"],
        "fielding_ovr": numeric_values["Fielding OVR"],
        "fitness": numeric_values["Fitness"],
        "rarity": rarity,
        "matches": 0,
        "runs": 0,
        "wickets": 0,
        "catches": 0,
        "price": numeric_values["Price"],
        "sell_price": numeric_values["Sell Price"],
        "image": raw["Image URL"].strip(),
    }

    return player, None


def player_exists(name):
    """
    Checks whether a player with the given name (case-insensitive)
    already exists in the players table.

    Returns:
        bool: True if a matching player exists, False otherwise.

    Raises:
        sqlite3.Error: if the database query fails.
    """
    conn = connect_db()

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM players WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def insert_player(player):
    """
    Inserts a new player row into the players table.

    Raises:
        sqlite3.Error: if the insert fails.
    """
    conn = connect_db()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO players (
                id,
                name,
                display_name,
                country,
                team,
                role,
                batting_style,
                bowling_style,
                ovr,
                batting_ovr,
                bowling_ovr,
                fielding_ovr,
                fitness,
                rarity,
                matches,
                runs,
                wickets,
                catches,
                price,
                sell_price,
                image
            ) VALUES (
                :id,
                :name,
                :display_name,
                :country,
                :team,
                :role,
                :batting_style,
                :bowling_style,
                :ovr,
                :batting_ovr,
                :bowling_ovr,
                :fielding_ovr,
                :fitness,
                :rarity,
                :matches,
                :runs,
                :wickets,
                :catches,
                :price,
                :sell_price,
                :image
            )
            """,
            player
        )
        conn.commit()
    finally:
        conn.close()


def build_preview_embed(player):
    """Builds the confirmation embed shown before saving."""
    embed = discord.Embed(
        title="📋 Confirm New Player",
        description="Reply **YES** to save, or **NO** to cancel.",
        color=discord.Color.orange()
    )

    embed.add_field(name="Player Name", value=player["name"], inline=True)
    embed.add_field(name="Country", value=player["country"], inline=True)
    embed.add_field(name="Team", value=player["team"], inline=True)

    embed.add_field(name="Role", value=player["role"], inline=True)
    embed.add_field(name="Batting Style", value=player["batting_style"], inline=True)
    embed.add_field(name="Bowling Style", value=player["bowling_style"], inline=True)

    embed.add_field(name="OVR", value=str(player["ovr"]), inline=True)
    embed.add_field(name="Batting OVR", value=str(player["batting_ovr"]), inline=True)
    embed.add_field(name="Bowling OVR", value=str(player["bowling_ovr"]), inline=True)

    embed.add_field(name="Fielding OVR", value=str(player["fielding_ovr"]), inline=True)
    embed.add_field(name="Fitness", value=str(player["fitness"]), inline=True)
    embed.add_field(name="Rarity", value=player["rarity"], inline=True)

    embed.add_field(name="Price", value=f"{player['price']:,}", inline=True)
    embed.add_field(name="Sell Price", value=f"{player['sell_price']:,}", inline=True)
    embed.set_image(url=player["image"])

    return embed


def build_success_embed(player):
    """Builds the green success embed shown after a player is saved."""
    embed = discord.Embed(
        title="✅ Player Added Successfully",
        description=f"**{player['name']}** has been added to the database.",
        color=discord.Color.green()
    )

    embed.add_field(name="Player ID", value=player["id"], inline=False)

    embed.add_field(name="Country", value=player["country"], inline=True)
    embed.add_field(name="Team", value=player["team"], inline=True)
    embed.add_field(name="Role", value=player["role"], inline=True)

    embed.add_field(name="Batting Style", value=player["batting_style"], inline=True)
    embed.add_field(name="Bowling Style", value=player["bowling_style"], inline=True)
    embed.add_field(name="Rarity", value=player["rarity"], inline=True)

    embed.add_field(name="OVR", value=str(player["ovr"]), inline=True)
    embed.add_field(name="Batting OVR", value=str(player["batting_ovr"]), inline=True)
    embed.add_field(name="Bowling OVR", value=str(player["bowling_ovr"]), inline=True)

    embed.add_field(name="Fielding OVR", value=str(player["fielding_ovr"]), inline=True)
    embed.add_field(name="Fitness", value=str(player["fitness"]), inline=True)
    embed.add_field(name="Price", value=f"{player['price']:,}", inline=True)

    embed.add_field(name="Sell Price", value=f"{player['sell_price']:,}", inline=True)
    embed.set_image(url=player["image"])

    return embed


def setup_addplayer(bot):

    @bot.command(name="addplayer")
    async def addplayer(ctx):

        if ctx.author.id != OWNER_ID:
            await ctx.send("❌ Only the bot owner can use this command.")
            return

        prompt = (
            "📋 **Reply with exactly 14 lines, in this order:**\n"
            "```\n"
            "Player Name\n"
            "Country\n"
            "Team\n"
            "Role\n"
            "Batting Style\n"
            "Bowling Style\n"
            "OVR\n"
            "Batting OVR\n"
            "Bowling OVR\n"
            "Fielding OVR\n"
            "Fitness\n"
            "Rarity\n"
            "Price\n"
            "Sell Price\n"
            "```\n"
            "**Example:**\n"
            "```\n"
            "Virat Kohli\n"
            "India\n"
            "RCB\n"
            "BAT\n"
            "Right Hand Bat\n"
            "Right Arm Medium\n"
            "92\n"
            "95\n"
            "42\n"
            "89\n"
            "97\n"
            "Legendary\n"
            "150000\n"
            "75000\n"
            "Image URL\n"
            "```\n"
            "⏳ You have 180 seconds to reply."
        )

        await ctx.send(prompt)

        def check_input(message):
            return message.author.id == ctx.author.id and message.channel.id == ctx.channel.id

        try:
            reply = await bot.wait_for(
                "message", timeout=INPUT_TIMEOUT_SECONDS, check=check_input
            )
        except asyncio.TimeoutError:
            await ctx.send("❌ Timed out. Please run `g!addplayer` again.")
            return

        player, error = parse_player_input(reply.content)

        if error is not None:
            await ctx.send(error)
            return

        try:
            if player_exists(player["name"]):
                await ctx.send(f"❌ A player named **{player['name']}** already exists in the database.")
                return
        except sqlite3.Error as e:
            await ctx.send(f"❌ A database error occurred while checking for duplicates: `{e}`")
            return

        preview_embed = build_preview_embed(player)
        await ctx.send(embed=preview_embed)

        def check_confirm(message):
            return (
                message.author.id == ctx.author.id
                and message.channel.id == ctx.channel.id
                and message.content.strip().upper() in ("YES", "NO")
            )

        try:
            confirmation = await bot.wait_for(
                "message", timeout=CONFIRM_TIMEOUT_SECONDS, check=check_confirm
            )
        except asyncio.TimeoutError:
            await ctx.send("❌ Confirmation timed out. Player was not saved.")
            return

        if confirmation.content.strip().upper() == "NO":
            await ctx.send("❌ Cancelled. Player was not saved.")
            return

        try:
            insert_player(player)
        except sqlite3.Error as e:
            await ctx.send(f"❌ A database error occurred while saving the player: `{e}`")
            return
            await log_action(
    bot=bot,
    title="🆕 Player Added",
    description=(
        f"**Player:** {player_name}\n"
        f"**OVR:** {ovr}\n"
        f"**Role:** {role}\n"
        f"**Rarity:** {rarity}"
    ),
    color=discord.Color.blue(),
    user=ctx.author,
    guild=ctx.guild,
    channel=ctx.channel
            )

        success_embed = build_success_embed(player)
        await ctx.send(embed=success_embed)
        