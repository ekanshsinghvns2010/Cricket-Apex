import discord
import json

from utils.match_utils import (
    get_match,
    load_matches,
    save_matches
)

USER_FILE = "users.json"


def load_users():
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


ROLE_ICONS = {
    "Aggressive Batter": "⚔",
    "Anchor Batter": "🛡",
    "Finisher": "💥",
    "Fast Bowler": "⚡",
    "Fast Swing Bowler": "🌪",
    "Spinner": "🌀",
    "Leg Spinner": "🌀",
    "Off Spinner": "🌀",
    "All-Rounder": "⭐",
    None: "❔"
}


async def build_lobby_embed(guild, match_id):

    match = get_match(match_id)

    users = load_users()

    embed = discord.Embed(
        title="🏏 CRICKET 11 • MATCH LOBBY",
        color=0x00C853
    )

    embed.add_field(
        name="🏟 Stadium",
        value=match["stadium"],
        inline=True
    )

    embed.add_field(
        name="🌍 Country",
        value=match["country"],
        inline=True
    )

    embed.add_field(
        name="🌦 Weather",
        value=match["weather"],
        inline=True
    )

    embed.add_field(
        name="🌱 Pitch",
        value=match["pitch"],
        inline=True
    )

    embed.add_field(
        name="🏏 Overs",
        value=str(match["overs"]),
        inline=True
    )

    embed.add_field(
        name="👥 Format",
        value=match["format"],
        inline=True
    )

    red = ""

    for uid in match["red_team"]:

        member = guild.get_member(int(uid))

        if member is None:
            continue

        role = users.get(uid, {}).get("role")

        icon = ROLE_ICONS.get(role, "❔")

        if uid == match["red_captain"]:
            red += f"👑 **{member.display_name}**\n{icon} {role}\n\n"
        else:
            red += f"**{member.display_name}**\n{icon} {role}\n\n"

    # Show Red Team bots
    for bot in match["red_bots"]:

        icon = ROLE_ICONS.get(bot["role"], "🤖")

        red += (
            f"🤖 **{bot['name']}**\n"
            f"{icon} {bot['role']}\n\n"
        )

    if red == "":
        red = "No players"

    blue = ""

    for uid in match["blue_team"]:

        member = guild.get_member(int(uid))

        if member is None:
            continue

        role = users.get(uid, {}).get("role")

        icon = ROLE_ICONS.get(role, "❔")

        if uid == match["blue_captain"]:
            blue += f"👑 **{member.display_name}**\n{icon} {role}\n\n"
        else:
            blue += f"**{member.display_name}**\n{icon} {role}\n\n"

    # Show Blue Team bots
    for bot in match["blue_bots"]:

        icon = ROLE_ICONS.get(bot["role"], "🤖")

        blue += (
            f"🤖 **{bot['name']}**\n"
            f"{icon} {bot['role']}\n\n"
        )

    if blue == "":
        blue = "No players"

    embed.add_field(
        name=f"🔴 Red Team ({len(match['red_team'])+len(match['red_bots'])}/{match['team_size']})",
        value=red,
        inline=True
    )

    embed.add_field(
        name=f"🔵 Blue Team ({len(match['blue_team'])+len(match['blue_bots'])}/{match['team_size']})",
        value=blue,
        inline=True
    )

    embed.add_field(
        name="Status",
        value="⏳ Waiting for players...",
        inline=False
    )

    embed.set_footer(
        text=f"Match ID: {match_id}"
    )

    return embed


class MatchLobbyView(discord.ui.View):

    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.match_id = str(match_id)

    @discord.ui.button(
        label="Join Red",
        style=discord.ButtonStyle.danger,
        emoji="🔴"
    )
    async def join_red(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        matches = load_matches()

        match = matches.get(self.match_id)

        if match is None:
            await interaction.response.send_message(
                "❌ This match no longer exists.",
                ephemeral=True
            )
            return

        uid = str(interaction.user.id)

        if uid in match["red_team"]:
            await interaction.response.send_message(
                "❌ You are already in Red Team.",
                ephemeral=True
            )
            return

        if uid in match["blue_team"]:
            await interaction.response.send_message(
                "❌ Leave Blue Team first.",
                ephemeral=True
            )
            return

        if len(match["red_team"]) >= match["team_size"]:
            await interaction.response.send_message(
                "❌ Red Team is full.",
                ephemeral=True
            )
            return

        match["red_team"].append(uid)

        save_matches(matches)

        embed = await build_lobby_embed(
            interaction.guild,
            self.match_id
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

        # Check if both teams are full
        if (
            len(match["red_team"]) == match["team_size"]
            and
            len(match["blue_team"]) == match["team_size"]
        ):
            print(f"🏏 Match {self.match_id} is ready to start!")

    @discord.ui.button(
        label="Join Blue",
        style=discord.ButtonStyle.primary,
        emoji="🔵"
    )
    async def join_blue(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        matches = load_matches()

        match = matches.get(self.match_id)

        if match is None:
            await interaction.response.send_message(
                "❌ This match no longer exists.",
                ephemeral=True
            )
            return

        uid = str(interaction.user.id)

        if uid in match["blue_team"]:
            await interaction.response.send_message(
                "❌ You are already in Blue Team.",
                ephemeral=True
            )
            return

        if uid in match["red_team"]:
            await interaction.response.send_message(
                "❌ Leave Red Team first.",
                ephemeral=True
            )
            return

        if len(match["blue_team"]) >= match["team_size"]:
            await interaction.response.send_message(
                "❌ Blue Team is full.",
                ephemeral=True
            )
            return

        match["blue_team"].append(uid)

        if match["blue_captain"] is None:
            match["blue_captain"] = uid

        save_matches(matches)

        embed = await build_lobby_embed(
            interaction.guild,
            self.match_id
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

        # Check if both teams are full
        if (
            len(match["red_team"]) == match["team_size"]
            and
            len(match["blue_team"]) == match["team_size"]
        ):
            print(f"🏏 Match {self.match_id} is ready to start!")

    @discord.ui.button(
        label="Leave Match",
        style=discord.ButtonStyle.secondary,
        emoji="🚪"
    )
    async def leave_match(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        matches = load_matches()

        match = matches.get(self.match_id)

        if match is None:
            await interaction.response.send_message(
                "❌ This match no longer exists.",
                ephemeral=True
            )
            return

        uid = str(interaction.user.id)

        # Creator leaves -> End Match
        if uid == match["creator"]:

            del matches[self.match_id]
            save_matches(matches)

            ended_embed = discord.Embed(
                title="🏏 MATCH ENDED",
                description="❌ The match creator left the lobby.\n\nThis match has been closed.",
                color=discord.Color.red()
            )

            for child in self.children:
                child.disabled = True

            await interaction.response.edit_message(
                embed=ended_embed,
                view=self
            )
            return

        if uid in match["red_team"]:
            match["red_team"].remove(uid)

        elif uid in match["blue_team"]:

            match["blue_team"].remove(uid)

            if match["blue_captain"] == uid:

                if len(match["blue_team"]) > 0:
                    match["blue_captain"] = match["blue_team"][0]
                else:
                    match["blue_captain"] = None

        else:
            await interaction.response.send_message(
                "❌ You are not in this match.",
                ephemeral=True
            )
            return

        save_matches(matches)

        embed = await build_lobby_embed(
            interaction.guild,
            self.match_id
        )

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )