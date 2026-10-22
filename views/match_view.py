
import discord

from utils.match_engine import (
    BATTING_SHOTS,
    BATTING_INTENTS,
    BOWLING_LENGTHS,
    bowling_variations,
    delivery_result,
)
from utils.match_utils import load_matches, save_matches


def get_player_id(player):
    if isinstance(player, dict):
        return str(player.get("id", player.get("player_id", "")))
    return str(player) if player is not None else ""


def get_player_name(player):
    if isinstance(player, dict):
        return player.get("display_name") or player.get("name") or "Unknown"
    return str(player) if player is not None else "Not selected"


def get_player(match, player_id):
    """Find a player in either team's confirmed XI."""
    player_id = get_player_id(player_id)

    for team in ("red", "blue"):
        for player in match.get(f"{team}_xi", []):
            if get_player_id(player) == player_id:
                return player

    return None


def build_match_embed(match_id):
    matches = load_matches()
    match = matches.get(str(match_id))

    if not match:
        return discord.Embed(
            title="Match not found",
            color=discord.Color.red(),
        )

    batting_team = match.get("batting_team", "red")
    bowling_team = match.get("bowling_team", "blue")

    batting_name = match.get(
        f"{batting_team}_name", batting_team.title()
    )
    bowling_name = match.get(
        f"{bowling_team}_name", bowling_team.title()
    )

    runs = int(match.get("runs", 0))
    wickets = int(match.get("wickets", 0))
    overs = int(match.get("overs_completed", 0))
    balls = int(match.get("balls_in_over", match.get("balls", 0)))

    embed = discord.Embed(
        title="🏏 Cricket Apex — Match Centre",
        description=f"**{batting_name}** vs **{bowling_name}**",
        color=discord.Color.green(),
    )

    embed.add_field(
        name="Score",
        value=f"**{runs}/{wickets}**",
        inline=True,
    )
    embed.add_field(
        name="Overs",
        value=f"{overs}.{balls} / {match.get('overs', 20)}",
        inline=True,
    )
    embed.add_field(
        name="Innings",
        value=str(match.get("innings", 1)),
        inline=True,
    )
    embed.add_field(
        name="🏏 Striker",
        value=get_player_name(match.get("striker")),
        inline=True,
    )
    embed.add_field(
        name="🏏 Non-striker",
        value=get_player_name(match.get("non_striker")),
        inline=True,
    )
    embed.add_field(
        name="🎯 Bowler",
        value=get_player_name(match.get("current_bowler")),
        inline=True,
    )

    if match.get("target") is not None:
        embed.add_field(
            name="Target",
            value=str(match["target"]),
            inline=True,
        )

    embed.add_field(
        name="Status",
        value=str(match.get("status", "unknown")).replace("_", " ").title(),
        inline=True,
    )

    return embed


class MatchView(discord.ui.View):
    """Interactive delivery controls for a live innings."""

    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.match_id = str(match_id)

        matches = load_matches()
        match = matches.get(self.match_id, {})

        self.add_item(DeliverySelect(self.match_id, "variation"))

        # Shot and intent are chosen by the batting captain.
        self.add_item(DeliverySelect(self.match_id, "shot"))
        self.add_item(DeliverySelect(self.match_id, "intent"))
        self.add_item(DeliverySelect(self.match_id, "length"))

        self.add_item(SubmitDeliveryButton(self.match_id))

    async def refresh(self, interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.followup.send(
                "This match could not be found.",
                ephemeral=True,
            )
            return

        await interaction.message.edit(
            embed=build_match_embed(self.match_id),
            view=MatchView(self.match_id),
        )


class DeliverySelect(discord.ui.Select):
    def __init__(self, match_id, selection_type):
        self.match_id = str(match_id)
        self.selection_type = selection_type

        matches = load_matches()
        match = matches.get(self.match_id, {})

        bowler = get_player(
            match, match.get("current_bowler")
        ) or {}

        if selection_type == "variation":
            options = [
                discord.SelectOption(label=value)
                for value in bowling_variations(bowler)
            ]
            placeholder = "Bowling captain: choose variation"

        elif selection_type == "shot":
            options = [
                discord.SelectOption(label=value)
                for value in BATTING_SHOTS
            ]
            placeholder = "Batting captain: choose shot"

        elif selection_type == "intent":
            options = [
                discord.SelectOption(label=value)
                for value in BATTING_INTENTS
            ]
            placeholder = "Batting captain: choose intent"

        else:
            options = [
                discord.SelectOption(label=value)
                for value in BOWLING_LENGTHS
            ]
            placeholder = "Bowling captain: choose length"

        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options[:25],
            custom_id=f"match_{selection_type}_{self.match_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match or match.get("status") != "live":
            await interaction.response.send_message(
                "This match is not live.",
                ephemeral=True,
            )
            return

        batting_team = match.get("batting_team", "red")
        bowling_team = match.get("bowling_team", "blue")

        if self.selection_type in ("shot", "intent"):
            captain = match.get(f"{batting_team}_captain")
            label = "batting"
        else:
            captain = match.get(f"{bowling_team}_captain")
            label = "bowling"

        if str(interaction.user.id) != str(captain):
            await interaction.response.send_message(
                f"Only the {label} captain can change this selection.",
                ephemeral=True,
            )
            return

        match.setdefault("delivery_choices", {})[
            self.selection_type
        ] = self.values[0]

        save_matches(matches)

        await interaction.response.send_message(
            f"Selected: **{self.values[0]}**",
            ephemeral=True,
        )


class SubmitDeliveryButton(discord.ui.Button):
    def __init__(self, match_id):
        self.match_id = str(match_id)

        super().__init__(
            label="Deliver Ball",
            style=discord.ButtonStyle.success,
            custom_id=f"match_deliver_{self.match_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match or match.get("status") != "live":
            await interaction.response.send_message(
                "This match is not live.",
                ephemeral=True,
            )
            return

        batting_team = match.get("batting_team", "red")
        bowling_team = match.get("bowling_team", "blue")

        batting_captain = match.get(f"{batting_team}_captain")
        bowling_captain = match.get(f"{bowling_team}_captain")

        if str(interaction.user.id) not in {
            str(batting_captain),
            str(bowling_captain),
        }:
            await interaction.response.send_message(
                "Only either team's captain can submit a delivery.",
                ephemeral=True,
            )
            return

        choices = match.get("delivery_choices", {})

        required = ("variation", "shot", "intent", "length")
        missing = [key for key in required if not choices.get(key)]

        if missing:
            await interaction.response.send_message(
                "Choose all delivery options first: "
                + ", ".join(missing),
                ephemeral=True,
            )
            return

        batter_id = match.get("striker")
        bowler_id = match.get("current_bowler")

        batter = get_player(match, batter_id)
        bowler = get_player(match, bowler_id)

        if not batter or not bowler:
            await interaction.response.send_message(
                "The striker or bowler is missing from the playing XI. "
                "Complete opening selection first.",
                ephemeral=True,
            )
            return

        result = delivery_result(
            batter=batter,
            bowler=bowler,
            variation=choices["variation"],
            length=choices["length"],
            shot=choices["shot"],
            intent=choices["intent"],
            pitch=match.get("pitch", "Normal"),
        )

        runs = int(result.get("runs", 0))
        match["runs"] = int(match.get("runs", 0)) + runs

        extras = match.setdefault("extras", {})
        extra_type = result.get("extra")

        if extra_type:
            extras[extra_type] = int(extras.get(extra_type, 0)) + runs

        if result.get("wicket"):
            match["wickets"] = int(match.get("wickets", 0)) + 1

            dismissed = match.setdefault("dismissed_players", [])
            dismissed.append(batter_id)

            # Clear striker so the next-batter selection must happen.
            match["striker"] = None
            match["status"] = "batter_selection"

        legal = bool(result.get("legal", True))

        if legal:
            total_balls = (
                int(match.get("overs_completed", 0)) * 6
                + int(match.get("balls_in_over", 0))
                + 1
            )

            match["overs_completed"] = total_balls // 6
            match["balls_in_over"] = total_balls % 6

            # Swap ends after an odd number of runs, except on a wicket
            # where the incoming batter selection handles the striker.
            if runs % 2 == 1 and not result.get("wicket"):
                match["striker"], match["non_striker"] = (
                    match.get("non_striker"),
                    match.get("striker"),
                )

            # Swap ends at the end of a completed over.
            if total_balls % 6 == 0 and not result.get("wicket"):
                match["striker"], match["non_striker"] = (
                    match.get("non_striker"),
                    match.get("striker"),
                )
                match["previous_bowler"] = bowler_id
                match["status"] = "bowler_selection"

        match["last_delivery"] = result.get("description", "Delivery complete.")
        match["delivery_choices"] = {}

        overs_limit = int(match.get("overs", 20))
        innings_over = (
            int(match.get("overs_completed", 0)) >= overs_limit
        )
        all_out = int(match.get("wickets", 0)) >= 10

        if innings_over or all_out:
            match["status"] = "innings_break"

        save_matches(matches)

        await interaction.response.edit_message(
            embed=build_match_embed(self.match_id),
            view=MatchView(self.match_id)
            if match.get("status") == "live"
            else None,
        )

        await interaction.followup.send(
            f"**{result.get('description', 'Delivery complete.')}**",
            ephemeral=False,
        )
