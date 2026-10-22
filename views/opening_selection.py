
import discord
from discord.ui import View, Select

from utils.match_utils import load_matches, save_matches


def get_player_id(player):
    if isinstance(player, dict):
        return str(player.get("id", ""))
    return str(player or "")


def get_player_name(player):
    if isinstance(player, dict):
        return player.get("display_name") or player.get("name", "Unknown")
    return str(player or "Not selected")


def get_team_xi(match, team):
    xi = match.get(f"{team}_xi", [])
    return xi if isinstance(xi, list) else []


def get_team_name(match, team):
    return match.get(f"{team}_name", team.title())


def find_player(xi, selected_id):
    return next(
        (p for p in xi if get_player_id(p) == str(selected_id)),
        None,
    )


def build_opening_embed(match):
    batting_team = match.get("batting_team", "red")
    bowling_team = match.get("bowling_team", "blue")

    striker = match.get("striker")
    non_striker = match.get("non_striker")
    bowler = match.get("current_bowler")

    embed = discord.Embed(
        title="🏏 Opening Players",
        description=(
            f"**Batting team:** {get_team_name(match, batting_team)}\n"
            f"**Bowling team:** {get_team_name(match, bowling_team)}\n\n"
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
            if get_player_id(player)
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
            custom_id=f"cricket_apex:{self.match_id}:{slot}",
        )

    async def callback(self, interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "Match not found.",
                ephemeral=True,
            )
            return

        batting_team = match.get("batting_team", "red")
        if batting_team != self.batting_team:
            await interaction.response.send_message(
                "The batting team has changed. Please reopen selection.",
                ephemeral=True,
            )
            return

        captain_id = str(match.get(f"{self.batting_team}_captain") or "")
        if str(interaction.user.id) != captain_id:
            await interaction.response.send_message(
                "Only the batting captain can choose opening batters.",
                ephemeral=True,
            )
            return

        if match.get("status") != "opening_selection":
            await interaction.response.send_message(
                "Opening selection is not active.",
                ephemeral=True,
            )
            return

        xi = get_team_xi(match, self.batting_team)
        player = find_player(xi, self.values[0])

        if not player:
            await interaction.response.send_message(
                "That player is not in your team's XI.",
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
                "Opening batters must be different players.",
                ephemeral=True,
            )
            return

        match[self.slot] = player
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
            if get_player_id(player)
        ]

        super().__init__(
            placeholder="Choose opening bowler",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"cricket_apex:{self.match_id}:opening_bowler",
        )

    async def callback(self, interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "Match not found.",
                ephemeral=True,
            )
            return

        bowling_team = match.get("bowling_team", "blue")
        if bowling_team != self.bowling_team:
            await interaction.response.send_message(
                "The bowling team has changed. Please reopen selection.",
                ephemeral=True,
            )
            return

        captain_id = str(match.get(f"{self.bowling_team}_captain") or "")
        if str(interaction.user.id) != captain_id:
            await interaction.response.send_message(
                "Only the bowling captain can choose the opening bowler.",
                ephemeral=True,
            )
            return

        if match.get("status") != "opening_selection":
            await interaction.response.send_message(
                "Opening selection is not active.",
                ephemeral=True,
            )
            return

        xi = get_team_xi(match, self.bowling_team)
        player = find_player(xi, self.values[0])

        if not player:
            await interaction.response.send_message(
                "That player is not in the bowling team's XI.",
                ephemeral=True,
            )
            return

        match["current_bowler"] = player
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

        batting_team = match.get("batting_team", "red")
        bowling_team = match.get("bowling_team", "blue")

        if not get_team_xi(match, batting_team):
            raise ValueError("Batting team's XI is empty.")
        if not get_team_xi(match, bowling_team):
            raise ValueError("Bowling team's XI is empty.")

        self.add_item(
            OpeningBatterSelect(self.match_id, batting_team, "striker")
        )
        self.add_item(
            OpeningBatterSelect(self.match_id, batting_team, "non_striker")
        )
        self.add_item(
            OpeningBowlerSelect(self.match_id, bowling_team)
        )

    @discord.ui.button(
        label="Start Innings",
        style=discord.ButtonStyle.success,
        emoji="🏏",
        custom_id="cricket_apex:start_innings",
        row=3,
    )
    async def start_innings(self, interaction, button):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "Match not found.",
                ephemeral=True,
            )
            return

        batting_team = match.get("batting_team", "red")
        bowling_team = match.get("bowling_team", "blue")

        captain_ids = {
            str(match.get(f"{batting_team}_captain") or ""),
            str(match.get(f"{bowling_team}_captain") or ""),
        }

        if str(interaction.user.id) not in captain_ids:
            await interaction.response.send_message(
                "Only either captain can start the innings.",
                ephemeral=True,
            )
            return

        if match.get("status") != "opening_selection":
            await interaction.response.send_message(
                "Opening selection is not active.",
                ephemeral=True,
            )
            return

        striker = match.get("striker")
        non_striker = match.get("non_striker")
        bowler = match.get("current_bowler")

        if not striker or not non_striker or not bowler:
            await interaction.response.send_message(
                "Choose both opening batters and the opening bowler first.",
                ephemeral=True,
            )
            return

        batting_ids = {
            get_player_id(p) for p in get_team_xi(match, batting_team)
        }
        bowling_ids = {
            get_player_id(p) for p in get_team_xi(match, bowling_team)
        }

        if (
            get_player_id(striker) not in batting_ids
            or get_player_id(non_striker) not in batting_ids
            or get_player_id(bowler) not in bowling_ids
        ):
            await interaction.response.send_message(
                "One or more selected players are not in the confirmed XI.",
                ephemeral=True,
            )
            return

        if get_player_id(striker) == get_player_id(non_striker):
            await interaction.response.send_message(
                "Opening batters must be different.",
                ephemeral=True,
            )
            return

        match["status"] = "live"
        match["state"] = "MATCH"
        match["interaction_stage"] = "variation"
        match.setdefault("innings", 1)
        match.setdefault("runs", 0)
        match.setdefault("wickets", 0)
        match.setdefault("overs_completed", 0)
        match.setdefault("balls_in_over", 0)
        match.setdefault("target", None)
        match["dismissed_players"] = []
        match.setdefault("bowler_overs", {})
        match.setdefault("recent_balls", [])
        match["batters"] = [striker, non_striker]

        save_matches(matches)

        # Build the actual live controls on the same message.
        from views.match_view import MatchView, build_match_embed

        await interaction.response.edit_message(
            content="🏏 **Innings started!**",
            embed=build_match_embed(self.match_id),
            view=MatchView(self.match_id),
        )


async def send_opening_selection(channel, match_id):
    matches = load_matches()
    match = matches.get(str(match_id))

    if not match:
        raise ValueError(f"Match {match_id} was not found.")

    if not (
        match.get("xi_confirmed", {}).get("red", False)
        and match.get("xi_confirmed", {}).get("blue", False)
    ):
        raise ValueError("Both captains must confirm their XIs first.")

    match["status"] = "opening_selection"
    match["state"] = "OPENING_SELECTION"
    match["interaction_stage"] = "opening_selection"
    save_matches(matches)

    return await channel.send(
        embed=build_opening_embed(match),
        view=OpeningSelectionView(str(match_id)),
    )
