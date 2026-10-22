
import discord
from discord.ui import View, Select

from utils.match_utils import load_matches, save_matches


def player_id(player):
    if isinstance(player, dict):
        return str(player.get("id", ""))
    return str(player or "")


def player_name(player):
    if isinstance(player, dict):
        return player.get("display_name") or player.get("name", "Unknown")
    return str(player or "Not selected")


def team_xi(match, team):
    xi = match.get(f"{team}_xi", [])
    return xi if isinstance(xi, list) else []


def team_name(match, team):
    return match.get(f"{team}_name", team.title())


def find_player(xi, selected_id):
    return next(
        (p for p in xi if player_id(p) == str(selected_id)),
        None,
    )


def build_opening_embed(match):
    batting_team = match.get("batting_team", "red")
    bowling_team = match.get("bowling_team", "blue")

    embed = discord.Embed(
        title=f"🏏 Innings {match.get('innings', 1)} — Opening Selection",
        description=(
            f"**Batting:** {team_name(match, batting_team)}\n"
            f"**Bowling:** {team_name(match, bowling_team)}\n\n"
            "The batting captain chooses two different batters. "
            "The bowling captain chooses the opening bowler."
        ),
        color=discord.Color.blurple(),
    )

    embed.add_field(
        name="Striker",
        value=player_name(match.get("striker")),
        inline=True,
    )
    embed.add_field(
        name="Non-striker",
        value=player_name(match.get("non_striker")),
        inline=True,
    )
    embed.add_field(
        name="Bowler",
        value=player_name(match.get("current_bowler")),
        inline=True,
    )

    if int(match.get("innings", 1)) == 2:
        embed.add_field(
            name="Target",
            value=str(match.get("target", 0)),
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
        xi = team_xi(match, batting_team)

        options = [
            discord.SelectOption(
                label=player_name(p)[:100],
                value=player_id(p),
            )
            for p in xi[:25]
            if player_id(p)
        ]

        super().__init__(
            placeholder=(
                "Choose opening striker"
                if slot == "striker"
                else "Choose opening non-striker"
            ),
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"apex:{self.match_id}:opening:{slot}",
            row=0 if slot == "striker" else 1,
        )

    async def callback(self, interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            return await interaction.response.send_message(
                "Match not found.", ephemeral=True
            )

        if match.get("status") != "opening_selection":
            return await interaction.response.send_message(
                "Opening selection is not active.", ephemeral=True
            )

        if match.get("batting_team") != self.batting_team:
            return await interaction.response.send_message(
                "The batting team has changed. Reopen selection.",
                ephemeral=True,
            )

        captain = str(match.get(f"{self.batting_team}_captain") or "")
        if str(interaction.user.id) != captain:
            return await interaction.response.send_message(
                "Only the batting captain can choose opening batters.",
                ephemeral=True,
            )

        selected = find_player(
            team_xi(match, self.batting_team),
            self.values[0],
        )
        if not selected:
            return await interaction.response.send_message(
                "That player is not in the confirmed XI.",
                ephemeral=True,
            )

        other_slot = (
            "non_striker" if self.slot == "striker" else "striker"
        )
        other = match.get(other_slot)

        if other and player_id(other) == player_id(selected):
            return await interaction.response.send_message(
                "Opening batters must be different players.",
                ephemeral=True,
            )

        match[self.slot] = selected
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
        xi = team_xi(match, bowling_team)

        options = [
            discord.SelectOption(
                label=player_name(p)[:100],
                value=player_id(p),
            )
            for p in xi[:25]
            if player_id(p)
        ]

        super().__init__(
            placeholder="Choose opening bowler",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"apex:{self.match_id}:opening:bowler",
            row=2,
        )

    async def callback(self, interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            return await interaction.response.send_message(
                "Match not found.", ephemeral=True
            )

        if match.get("status") != "opening_selection":
            return await interaction.response.send_message(
                "Opening selection is not active.", ephemeral=True
            )

        if match.get("bowling_team") != self.bowling_team:
            return await interaction.response.send_message(
                "The bowling team has changed. Reopen selection.",
                ephemeral=True,
            )

        captain = str(match.get(f"{self.bowling_team}_captain") or "")
        if str(interaction.user.id) != captain:
            return await interaction.response.send_message(
                "Only the bowling captain can choose the bowler.",
                ephemeral=True,
            )

        selected = find_player(
            team_xi(match, self.bowling_team),
            self.values[0],
        )
        if not selected:
            return await interaction.response.send_message(
                "That player is not in the confirmed XI.",
                ephemeral=True,
            )

        match["current_bowler"] = selected
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

        batting = match.get("batting_team", "red")
        bowling = match.get("bowling_team", "blue")

        if not team_xi(match, batting) or not team_xi(match, bowling):
            raise ValueError("Both teams need a confirmed XI.")

        self.add_item(
            OpeningBatterSelect(self.match_id, batting, "striker")
        )
        self.add_item(
            OpeningBatterSelect(self.match_id, batting, "non_striker")
        )
        self.add_item(OpeningBowlerSelect(self.match_id, bowling))

    @discord.ui.button(
        label="Start Innings",
        style=discord.ButtonStyle.success,
        emoji="🏏",
        custom_id="apex:start_innings",
        row=3,
    )
    async def start_innings(self, interaction, button):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            return await interaction.response.send_message(
                "Match not found.", ephemeral=True
            )

        if match.get("status") != "opening_selection":
            return await interaction.response.send_message(
                "Opening selection is not active.", ephemeral=True
            )

        batting = match.get("batting_team", "red")
        bowling = match.get("bowling_team", "blue")

        allowed = {
            str(match.get(f"{batting}_captain") or ""),
            str(match.get(f"{bowling}_captain") or ""),
        }
        if str(interaction.user.id) not in allowed:
            return await interaction.response.send_message(
                "Only a captain can start the innings.", ephemeral=True
            )

        striker = match.get("striker")
        non_striker = match.get("non_striker")
        bowler = match.get("current_bowler")

        if not striker or not non_striker or not bowler:
            return await interaction.response.send_message(
                "Choose both batters and the bowler first.",
                ephemeral=True,
            )

        batting_ids = {player_id(p) for p in team_xi(match, batting)}
        bowling_ids = {player_id(p) for p in team_xi(match, bowling)}

        if (
            player_id(striker) not in batting_ids
            or player_id(non_striker) not in batting_ids
            or player_id(bowler) not in bowling_ids
        ):
            return await interaction.response.send_message(
                "A selected player is not in the confirmed XI.",
                ephemeral=True,
            )

        if player_id(striker) == player_id(non_striker):
            return await interaction.response.send_message(
                "Opening batters must be different.",
                ephemeral=True,
            )

        innings = int(match.get("innings", 1))

        # Reset per-innings values without erasing the target or team scores.
        match["runs"] = 0
        match["wickets"] = 0
        match["overs_completed"] = 0
        match["balls_in_over"] = 0
        match["balls"] = 0
        match["dismissed_players"] = []
        match["batted_players"] = [
            player_id(striker),
            player_id(non_striker),
        ]
        match["dismissed_slot"] = None
        match["batting_stats"] = {}
        match["bowling_stats"] = {}
        match["extras"] = {}
        match["previous_bowler"] = None
        match["status"] = "live"
        match["state"] = "MATCH"
        match["interaction_stage"] = "variation"

        save_matches(matches)

        from views.match_view import MatchView, build_match_embed

        await interaction.response.edit_message(
            content=f"🏏 **Innings {innings} has started!**",
            embed=build_match_embed(self.match_id),
            view=MatchView(self.match_id),
        )


async def send_opening_selection(channel, match_id):
    matches = load_matches()
    key = str(match_id)
    match = matches.get(key)

    if not match:
        raise ValueError(f"Match {match_id} not found.")

    confirmed = match.get("xi_confirmed", {})
    if not confirmed.get("red") or not confirmed.get("blue"):
        raise ValueError("Both captains must confirm their XIs first.")

    match["status"] = "opening_selection"
    match["state"] = "OPENING_SELECTION"
    match["interaction_stage"] = "opening_selection"
    match["striker"] = None
    match["non_striker"] = None
    match["current_bowler"] = None

    save_matches(matches)

    return await channel.send(
        embed=build_opening_embed(match),
        view=OpeningSelectionView(key),
    )
