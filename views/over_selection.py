
# views/over_selection.py

import discord
from discord.ui import View, Select

from utils.match_utils import load_matches, save_matches


def player_id(player):
    if isinstance(player, dict):
        return str(player.get("id", ""))
    return str(player) if player is not None else ""


def player_name(player):
    if isinstance(player, dict):
        return (
            player.get("display_name")
            or player.get("name")
            or "Unknown"
        )
    return str(player) if player is not None else "Unknown"


def team_xi(match, team):
    xi = match.get(f"{team}_xi", [])
    return xi if isinstance(xi, list) else []


def build_bowler_embed(match):
    bowling_team = match.get("bowling_team", "team2")
    previous_bowler = match.get("previous_bowler")
    current_bowler = match.get("current_bowler")

    embed = discord.Embed(
        title="🎯 Select the Next Bowler",
        description=(
            f"**Bowling team:** "
            f"{match.get(f'{bowling_team}_name', bowling_team)}\n"
            f"**Completed overs:** {match.get('overs', 0)}\n\n"
            "The bowling captain must choose a bowler for the next over."
        ),
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="Previous over",
        value=(
            player_name(previous_bowler)
            if previous_bowler
            else "None"
        ),
        inline=True,
    )

    embed.add_field(
        name="Next bowler",
        value=(
            player_name(current_bowler)
            if current_bowler
            else "Not selected"
        ),
        inline=True,
    )

    return embed


class NextBowlerSelect(Select):
    def __init__(self, match_id):
        self.match_id = str(match_id)

        matches = load_matches()
        match = matches.get(self.match_id, {})

        bowling_team = match.get("bowling_team", "team2")
        xi = team_xi(match, bowling_team)
        previous = match.get("previous_bowler")

        previous_id = player_id(previous)

        # Discord select menus allow a maximum of 25 options.
        eligible = [
            player
            for player in xi
            if player_id(player)
            and player_id(player) != previous_id
        ][:25]

        options = [
            discord.SelectOption(
                label=player_name(player)[:100],
                value=player_id(player),
                description=f"Player ID: {player_id(player)}"[:100],
            )
            for player in eligible
        ]

        super().__init__(
            placeholder="Choose the bowler for the next over",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"cricket_apex:next_bowler:{self.match_id}",
            disabled=not options,
        )

    async def callback(self, interaction: discord.Interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "Match not found.",
                ephemeral=True,
            )
            return

        if match.get("status") != "bowler_selection":
            await interaction.response.send_message(
                "Bowler selection is not open.",
                ephemeral=True,
            )
            return

        bowling_team = match.get("bowling_team", "team2")
        captain_id = str(
            match.get(f"{bowling_team}_captain", "")
        )

        if str(interaction.user.id) != captain_id:
            await interaction.response.send_message(
                "Only the bowling captain can select the next bowler.",
                ephemeral=True,
            )
            return

        xi = team_xi(match, bowling_team)
        selected_id = str(self.values[0])

        # Resolve the selection against the current XI, not just
        # the options originally displayed in Discord.
        selected = next(
            (
                player
                for player in xi
                if player_id(player) == selected_id
            ),
            None,
        )

        if selected is None:
            await interaction.response.send_message(
                "That player is not in the bowling team's XI.",
                ephemeral=True,
            )
            return

        previous = match.get("previous_bowler")

        if (
            previous
            and player_id(previous) == player_id(selected)
        ):
            await interaction.response.send_message(
                "A bowler cannot bowl consecutive overs.",
                ephemeral=True,
            )
            return

        match["current_bowler"] = selected
        match["interaction_stage"] = "variation"
        match["status"] = "live"

        save_matches(matches)

        await interaction.response.edit_message(
            content="✅ Next bowler selected. The next over is ready.",
            embed=build_bowler_embed(match),
            view=None,
        )


class NextBowlerView(View):
    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.match_id = str(match_id)
        self.add_item(NextBowlerSelect(self.match_id))


async def send_next_bowler_selection(channel, match_id):
    matches = load_matches()
    match = matches.get(str(match_id))

    if not match:
        raise ValueError(f"Match {match_id} was not found.")

    if match.get("status") != "bowler_selection":
        raise ValueError("This match is not waiting for a bowler.")

    bowling_team = match.get("bowling_team", "team2")
    xi = team_xi(match, bowling_team)
    previous = match.get("previous_bowler")
    previous_id = player_id(previous)

    eligible = [
        player
        for player in xi
        if player_id(player)
        and player_id(player) != previous_id
    ]

    if not eligible:
        raise ValueError(
            "No eligible bowler is available in the bowling team's XI."
        )

    return await channel.send(
        embed=build_bowler_embed(match),
        view=NextBowlerView(str(match_id)),
    )
