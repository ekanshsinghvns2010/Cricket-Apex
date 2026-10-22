import discord
import json

from utils.match_utils import get_match, load_matches, save_matches

USER_FILE = "users.json"


def load_users():
    try:
        with open(USER_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
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

    if match is None:
        raise ValueError(f"Match {match_id} not found")

    users = load_users()

    embed = discord.Embed(
        title="🏏 CRICKET 11 • MATCH LOBBY",
        color=0x00C853
    )

    embed.add_field(
        name="🏟 Stadium",
        value=match.get("stadium", "Unknown"),
        inline=True
    )
    embed.add_field(
        name="🌍 Country",
        value=match.get("country", "Unknown"),
        inline=True
    )
    embed.add_field(
        name="🌦 Weather",
        value=match.get("weather", "Unknown"),
        inline=True
    )
    embed.add_field(
        name="🌱 Pitch",
        value=match.get("pitch", "Unknown"),
        inline=True
    )
    embed.add_field(
        name="🏏 Overs",
        value=str(match.get("overs", "?")),
        inline=True
    )
    embed.add_field(
        name="👥 Format",
        value=match.get("format", "Unknown"),
        inline=True
    )

    # Build Red Team display.
    red = ""

    for uid in match.get("red_team", []):
        member = guild.get_member(int(uid)) if guild else None
        player_name = member.display_name if member else f"Player {uid[-4:]}"
        role = users.get(uid, {}).get("role")
        icon = ROLE_ICONS.get(role, "❔")

        if uid == match.get("red_captain"):
            red += f"👑 **{player_name}**\n{icon} {role or 'Role not set'}\n\n"
        else:
            red += f"**{player_name}**\n{icon} {role or 'Role not set'}\n\n"

    for player in match.get("red_bots", []):
        role = player.get("role")
        red += (
            f"🤖 **{player.get('name', 'Bot')}**\n"
            f"{ROLE_ICONS.get(role, '🤖')} {role or 'Unknown role'}\n\n"
        )

    if not red:
        red = "No players"

    # Build Blue Team display.
    blue = ""

    for uid in match.get("blue_team", []):
        member = guild.get_member(int(uid)) if guild else None
        player_name = member.display_name if member else f"Player {uid[-4:]}"
        role = users.get(uid, {}).get("role")
        icon = ROLE_ICONS.get(role, "❔")

        if uid == match.get("blue_captain"):
            blue += f"👑 **{player_name}**\n{icon} {role or 'Role not set'}\n\n"
        else:
            blue += f"**{player_name}**\n{icon} {role or 'Role not set'}\n\n"

    for player in match.get("blue_bots", []):
        role = player.get("role")
        blue += (
            f"🤖 **{player.get('name', 'Bot')}**\n"
            f"{ROLE_ICONS.get(role, '🤖')} {role or 'Unknown role'}\n\n"
        )

    if not blue:
        blue = "No players"

    team_size = match.get("team_size", 0)
    red_total = len(match.get("red_team", [])) + len(match.get("red_bots", []))
    blue_total = len(match.get("blue_team", [])) + len(match.get("blue_bots", []))

    embed.add_field(
        name=f"🔴 Red Team ({red_total}/{team_size})",
        value=red,
        inline=True
    )
    embed.add_field(
        name=f"🔵 Blue Team ({blue_total}/{team_size})",
        value=blue,
        inline=True
    )
    embed.add_field(
        name="Status",
        value="⏳ Waiting for players...",
        inline=False
    )
    embed.set_footer(text=f"Match ID: {match_id}")

    return embed


class MatchLobbyView(discord.ui.View):
    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.match_id = str(match_id)

    async def _join(self, interaction, team_name):
        matches = load_matches()
        match = matches.get(self.match_id)

        if match is None:
            await interaction.response.send_message(
                "❌ This match no longer exists.",
                ephemeral=True
            )
            return

        if match.get("status") != "lobby":
            await interaction.response.send_message(
                "❌ This match is already starting or has started.",
                ephemeral=True
            )
            return

        uid = str(interaction.user.id)
        own_team_key = f"{team_name}_team"
        other_team_key = "blue_team" if team_name == "red" else "red_team"

        own_team = match.setdefault(own_team_key, [])
        other_team = match.setdefault(other_team_key, [])
        own_bots = match.setdefault(f"{team_name}_bots", [])

        if uid in own_team:
            await interaction.response.send_message(
                f"❌ You are already in {team_name.title()} Team.",
                ephemeral=True
            )
            return

        if uid in other_team:
            other_name = "Blue" if team_name == "red" else "Red"
            await interaction.response.send_message(
                f"❌ Leave {other_name} Team first.",
                ephemeral=True
            )
            return

        if len(own_team) + len(own_bots) >= match["team_size"]:
            await interaction.response.send_message(
                f"❌ {team_name.title()} Team is full.",
                ephemeral=True
            )
            return

        own_team.append(uid)

        if team_name == "red" and match.get("red_captain") is None:
            match["red_captain"] = uid

        if team_name == "blue" and match.get("blue_captain") is None:
            match["blue_captain"] = uid

        save_matches(matches)

        embed = await build_lobby_embed(interaction.guild, self.match_id)

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )

        # Do not start countdown here.
        # The developer's g!fill command handles filling and countdown.

    @discord.ui.button(
        label="Join Red",
        style=discord.ButtonStyle.danger,
        emoji="🔴"
    )
    async def join_red(self, interaction, button):
        await self._join(interaction, "red")

    @discord.ui.button(
        label="Join Blue",
        style=discord.ButtonStyle.primary,
        emoji="🔵"
    )
    async def join_blue(self, interaction, button):
        await self._join(interaction, "blue")

    @discord.ui.button(
        label="Leave Match",
        style=discord.ButtonStyle.secondary,
        emoji="🚪"
    )
    async def leave_match(self, interaction, button):
        matches = load_matches()
        match = matches.get(self.match_id)

        if match is None:
            await interaction.response.send_message(
                "❌ This match no longer exists.",
                ephemeral=True
            )
            return

        if match.get("status") != "lobby":
            await interaction.response.send_message(
                "❌ This match has already started.",
                ephemeral=True
            )
            return

        uid = str(interaction.user.id)

        # If the creator leaves, close the lobby.
        if uid == match.get("creator"):
            del matches[self.match_id]
            save_matches(matches)

            ended_embed = discord.Embed(
                title="🏏 MATCH ENDED",
                description=(
                    "❌ The match creator left the lobby.\n\n"
                    "This match has been closed."
                ),
                color=discord.Color.red()
            )

            for child in self.children:
                child.disabled = True

            await interaction.response.edit_message(
                embed=ended_embed,
                view=self
            )
            return

        if uid in match.get("red_team", []):
            match["red_team"].remove(uid)

            if match.get("red_captain") == uid:
                match["red_captain"] = (
                    match["red_team"][0]
                    if match["red_team"]
                    else None
                )

        elif uid in match.get("blue_team", []):
            match["blue_team"].remove(uid)

            if match.get("blue_captain") == uid:
                match["blue_captain"] = (
                    match["blue_team"][0]
                    if match["blue_team"]
                    else None
                )

        else:
            await interaction.response.send_message(
                "❌ You are not in this match.",
                ephemeral=True
            )
            return

        save_matches(matches)

        embed = await build_lobby_embed(interaction.guild, self.match_id)

        await interaction.response.edit_message(
            embed=embed,
            view=self
        )