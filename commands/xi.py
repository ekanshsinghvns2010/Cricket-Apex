import discord
from discord.ext import commands
import json

from database import connect_db

USERS_FILE = "users.json"

ROLE_ORDER = {
    "BAT": 1,
    "WK": 2,
    "AR": 3,
    "BOWL": 4
}


COUNTRY_FLAGS = {
    "India": "🇮🇳",
    "Pakistan": "🇵🇰",
    "Australia": "🇦🇺",
    "England": "🏴",
    "South Africa": "🇿🇦",
    "Bangladesh": "🇧🇩",
    "Afghanistan": "🇦🇫",
    "Sri Lanka": "🇱🇰",
    "New Zealand": "🇳🇿",
    "West Indies": "🏝️",
}


CARD_EMOJIS = {
    "Common": "<:common:1526962292804026418>",
    "Rare": "🟦",
    "Epic": "🟪",
    "Legendary": "🟨",
    "Icon": "🟥"
}


BOWLING_EMOJIS = {
    "Right Arm Fast": "⚡",
    "Left Arm Fast": "⚡",
    "Right Arm Medium": "🎯",
    "Left Arm Medium": "🎯",
    "Off Spin": "🌀",
    "Offspin": "🌀",
    "Leg Spin": "🌪️",
    "Legspin": "🌪️",
    "Left Arm Orthodox": "🌀",
    "Chinaman": "🌪️"
}


def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def get_owned_players(user_id):
    users = load_users()

    profile = users.get(str(user_id))

    if profile is None:
        return []

    owned_ids = profile.get("cards", [])

    if not owned_ids:
        return []

    conn = connect_db()

    try:
        cursor = conn.cursor()

        players = []

        for player_id in owned_ids:
            cursor.execute(
                "SELECT * FROM players WHERE id=?",
                (player_id,)
            )

            row = cursor.fetchone()

            if row:
                players.append(dict(row))

        players.sort(
            key=lambda p: (
                ROLE_ORDER.get(p["role"], 99),
                -p["ovr"]
            )
        )

        return players

    finally:
        conn.close()


def calculate_team_ovr(players):
    if not players:
        return 0

    total = sum(player["ovr"] for player in players)

    return round(total / len(players))


def get_flag(country):
    return COUNTRY_FLAGS.get(country, "🏳️")


def get_card_emoji(rarity):
    return CARD_EMOJIS.get(rarity, "🟩")


def get_bowling_emoji(style):
    return BOWLING_EMOJIS.get(style, "🏏")


def format_player(player):
    flag = get_flag(player["country"])
    card = get_card_emoji(player["rarity"])
    bowl = get_bowling_emoji(player["bowling_style"])

    return (
        f"{flag} | {card} | "
        f"**`{player['display_name'][:15]:^15}`** | "
        f"`{player['ovr']:>2}` | "
        f"`{player['batting_ovr']:>2}` | "
        f"`{player['bowling_ovr']:>2}` | "
        f"{bowl}"
    )


def split_roles(players):
    bat = []
    wk = []
    ar = []
    bowl = []

    for player in players:

        if player["role"] == "BAT":
            bat.append(player)

        elif player["role"] == "WK":
            wk.append(player)

        elif player["role"] == "AR":
            ar.append(player)

        elif player["role"] == "BOWL":
            bowl.append(player)

    return bat, wk, ar, bowl

class XIView(discord.ui.View):

    def __init__(self, players):
        super().__init__(timeout=180)

        self.players = players

    @discord.ui.button(
        label="Playing XI",
        style=discord.ButtonStyle.green,
        emoji="🏏"
    )
    async def playing_xi(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        xi = self.players[:11]

        bat, wk, ar, bowl = split_roles(xi)

        description = ""

        description += (
            "`Country` | `Card` | `Player` | "
            "`OVR` | `BAT` | `BOWL`\n\n"
        )

        if bat:
            description += "__**BATTERS**__\n"

            for player in bat:
                description += format_player(player) + "\n"

            description += "\n"

        if wk:
            description += "__**WICKET KEEPERS**__\n"

            for player in wk:
                description += format_player(player) + "\n"

            description += "\n"

        if ar:
            description += "__**ALL-ROUNDERS**__\n"

            for player in ar:
                description += format_player(player) + "\n"

            description += "\n"

        if bowl:
            description += "__**BOWLERS**__\n"

            for player in bowl:
                description += format_player(player) + "\n"

            description += "\n"

        if len(xi) == 11:
            description += "✅ XI is valid for match."
        else:
            description += (
                f"❌ XI incomplete "
                f"({len(xi)}/11 Players)"
            )

        embed = discord.Embed(
            title="🏏 Playing XI",
            description=description,
            color=discord.Color.green()
        )

        embed.set_footer(
            text=f"Team OVR : {calculate_team_ovr(xi)}"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

    @discord.ui.button(
        label="Substitutes",
        style=discord.ButtonStyle.blurple,
        emoji="🪑"
    )
    async def substitutes(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        subs = self.players[11:]

        if not subs:

            embed = discord.Embed(
                title="🪑 Substitutes",
                description="You don't have any substitute players.",
                color=discord.Color.orange()
            )

            await interaction.response.edit_message(
                embed=embed,
                view=self
            )

            return

        text = ""

        for index, player in enumerate(subs, start=1):

            text += (
                f"**{index}.** "
                f"{format_player(player)}\n"
            )

        embed = discord.Embed(
            title="🪑 Substitute Players",
            description=text,
            color=discord.Color.blurple()
        )

        embed.set_footer(
            text=f"{len(subs)} Substitute Players"
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

def setup_xi(bot):

    @bot.command(name="xi")
    async def xi(ctx):

        players = get_owned_players(ctx.author.id)
        for p in players:
            print(p["name"], p["role"])

        if not players:
            await ctx.send(
                "❌ You don't own any players.\n"
                "Buy players using `g!buy` first."
            )
            return

        playing_xi = players[:11]

        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s XI",
            color=discord.Color.blue()
        )

        embed.description = (
            f"⭐ **Team OVR:** {calculate_team_ovr(playing_xi)}\n"
            f"👥 **Players Owned:** {len(players)}\n\n"
            "Press a button below to view your team."
        )

        embed.add_field(
            name="🏏 Playing XI",
            value=f"{min(len(players),11)}/11 Players",
            inline=True
        )

        embed.add_field(
            name="🪑 Substitutes",
            value=str(max(0, len(players) - 11)),
            inline=True
        )

        embed.add_field(
            name="📋 Status",
            value=(
                "✅ Ready for Match"
                if len(playing_xi) == 11
                else "❌ XI Incomplete"
            ),
            inline=False
        )

        embed.set_footer(
            text="Use the buttons below to switch between Playing XI and Substitutes."
        )

        view = XIView(players)

        await ctx.send(
            embed=embed,
            view=view
        )