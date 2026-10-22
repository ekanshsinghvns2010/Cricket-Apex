
# views/opening_selection.py

import discord
from discord.ui import View, Select

from utils.match_utils import load_matches, save_matches


def get_player_id(player):
    if isinstance(player, dict):
        return str(player.get("id", ""))
    return str(player)


def get_player_name(player):
    if isinstance(player, dict):
        return player.get("display_name") or player.get("name", "Unknown")
    return str(player)


def get_team_xi(match, team):
    xi = match.get(f"{team}_xi", [])
    return xi if isinstance(xi, list) else []


def get_team_name(match, team):
    return match.get(
        f"{team}_name",
        team.replace("_", " ").title(),
    )


def find_player(xi, player_id):
    return next(
        (p for p in xi if get_player_id(p) == str(player_id)),
        None,
    )


def build_opening_embed(match):
    batting_team = match.get("batting_team", "team1")
    bowling_team = match.get("bowling_team", "team2")

    striker = match.get("striker")
    non_striker = match.get("non_striker")
    bowler = match.get("current_bowler")

    embed = discord.Embed(
        title="🏏 Choose Opening Players",
        description=(
            f"**Batting:** {get_team_name(match, batting_team)}\n"
            f"**Bowling:** {get_team_name(match, bowling_team)}\n\n"
            "The batting captain chooses two different opening batters. "
            "The bowling captain chooses the opening bowler."
        ),
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="Striker",
        value=get_player_name(striker) if striker else "Not selected",
        inline=True,
    )
    embed.add_field(
        name="Non-striker",
        value=get_player_name(non_striker) if non_striker else "Not selected",
        inline=True,
    )
    embed.add_field(
        name="Opening bowler",
        value=get_player_name(bowler) if bowler else "Not selected",
        inline=True,
    )

    return embed


class OpeningBatterSelect(Select):
    def __init__(self, match_id, batting_team, slot):
        self.match_id = str(match_id)
        self.batting_team = batting_team
        self.slot = slot

        matches = load_matches()
        match = matches.get(self.match_id, {})
        xi = get_team_xi(match, batting_team)

        options = [
            discord.SelectOption(
                label=get_player_name(player)[:100],
                value=get_player_id(player),
                description=f"Player ID: {get_player_id(player)}"[:100],
            )
            for player in xi[:25]
        ]

        super().__init__(
            placeholder=(
                "Select opening striker"
                if slot == "striker"
                else "Select opening non-striker"
            ),
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"cricket_apex:opening_{slot}:{self.match_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "Match not found.", ephemeral=True
            )
            return

        captain = str(match.get(f"{self.batting_team}_captain", ""))

        if str(interaction.user.id) != captain:
            await interaction.response.send_message(
                "Only the batting captain can choose the opening batters.",
                ephemeral=True,
            )
            return

        if match.get("status") not in {
            "ready_to_play",
            "opening_selection",
        }:
            await interaction.response.send_message(
                "Opening selection is not open.", ephemeral=True
            )
            return

        xi = get_team_xi(match, self.batting_team)
        player = find_player(xi, self.values[0])

        if not player:
            await interaction.response.send_message(
                "That player is not in your team's confirmed XI.",
                ephemeral=True,
            )
            return

        other_slot = (
            "non_striker" if self.slot == "striker" else "striker"
        )
        other_player = match.get(other_slot)

        if (
            other_player
            and get_player_id(other_player) == get_player_id(player)
        ):
            await interaction.response.send_message(
                "The opening batters must be different players.",
                ephemeral=True,
            )
            return

        match[self.slot] = player
        match["status"] = "opening_selection"
        match["interaction_stage"] = "opening_selection"
        save_matches(matches)

        await interaction.response.edit_message(
            embed=build_opening_embed(match),
            view=self.view,
        )


class OpeningBowlerSelect(Select):
    def __init__(self, match_id, bowling_team):
        self.match_id = str(match_id)
        self.bowling_team = bowling_team

        matches = load_matches()
        match = matches.get(self.match_id, {})
        xi = get_team_xi(match, bowling_team)

        options = [
            discord.SelectOption(
                label=get_player_name(player)[:100],
                value=get_player_id(player),
                description=f"Player ID: {get_player_id(player)}"[:100],
            )
            for player in xi[:25]
        ]

        super().__init__(
            placeholder="Select opening bowler",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"cricket_apex:opening_bowler:{self.match_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "Match not found.", ephemeral=True
            )
            return

        captain = str(match.get(f"{self.bowling_team}_captain", ""))

        if str(interaction.user.id) != captain:
            await interaction.response.send_message(
                "Only the bowling captain can select the bowler.",
                ephemeral=True,
            )
            return

        if match.get("status") not in {
            "ready_to_play",
            "opening_selection",
        }:
            await interaction.response.send_message(
                "Opening selection is not open.", ephemeral=True
            )
            return

        xi = get_team_xi(match, self.bowling_team)
        player = find_player(xi, self.values[0])

        if not player:
            await interaction.response.send_message(
                "That player is not in the bowling team's confirmed XI.",
                ephemeral=True,
            )
            return

        match["current_bowler"] = player
        match["status"] = "opening_selection"
        match["interaction_stage"] = "opening_selection"
        save_matches(matches)

        await interaction.response.edit_message(
            embed=build_opening_embed(match),
            view=self.view,
        )


class OpeningSelectionView(View):
    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.match_id = str(match_id)

        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            raise ValueError(f"Match {self.match_id} not found.")

        batting_team = match.get("batting_team", "team1")
        bowling_team = match.get("bowling_team", "team2")

        self.add_item(
            OpeningBatterSelect(
                self.match_id, batting_team, "striker"
            )
        )
        self.add_item(
            OpeningBatterSelect(
                self.match_id, batting_team, "non_striker"
            )
        )
        self.add_item(
            OpeningBowlerSelect(
                self.match_id, bowling_team
            )
        )

    @discord.ui.button(
        label="Start Innings",
        style=discord.ButtonStyle.success,
        emoji="🏏",
        custom_id="cricket_apex:start_innings",
        row=3,
    )
    async def start_innings(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "Match not found.", ephemeral=True
            )
            return

        batting_team = match.get("batting_team", "team1")
        bowling_team = match.get("bowling_team", "team2")

        if str(interaction.user.id) not in {
            str(match.get(f"{batting_team}_captain", "")),
            str(match.get(f"{bowling_team}_captain", "")),
        }:
            await interaction.response.send_message(
                "Only either captain can start the innings.",
                ephemeral=True,
            )
            return

        if match.get("status") != "opening_selection":
            await interaction.response.send_message(
                "Opening selection is not active.", ephemeral=True
            )
            return

        striker = match.get("striker")
        non_striker = match.get("non_striker")
        bowler = match.get("current_bowler")

        if not striker or not non_striker or not bowler:
            await interaction.response.send_message(
                "Select both opening batters and the opening bowler first.",
                ephemeral=True,
            )
            return

        if get_player_id(striker) == get_player_id(non_striker):
            await interaction.response.send_message(
                "The opening batters must be different.",
                ephemeral=True,
            )
            return

        match["status"] = "live"
        match["interaction_stage"] = "variation"
        match.setdefault("runs", 0)
        match.setdefault("wickets", 0)
        match.setdefault("overs", 0)
        match.setdefault("balls", 0)
        match.setdefault("dismissed_players", [])
        match.setdefault("bowler_overs", {})
        save_matches(matches)

        await interaction.response.edit_message(
            content="🏏 Innings started! Continue to the match controls.",
            embed=build_opening_embed(match),
            view=None,
        )

        await interaction.followup.send(
            "Opening players confirmed. Connect your `MatchView` here "
            "to display the ball-by-ball controls.",
            ephemeral=True,
        )


async def send_opening_selection(channel, match_id):
    matches = load_matches()
    match = matches.get(str(match_id))

    if not match:
        raise ValueError(f"Match {match_id} was not found.")

    match["status"] = "opening_selection"
    match["interaction_stage"] = "opening_selection"
    save_matches(matches)

    return await channel.send(
        embed=build_opening_embed(match),
        view=OpeningSelectionView(str(match_id)),
    )
