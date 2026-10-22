
import discord

from utils.match_engine import (
    BATTING_SHOTS,
    BATTING_INTENTS,
    BOWLING_LENGTHS,
    bowling_variations,
    delivery_result,
)
from utils.match_utils import load_matches, save_matches
from utils.innings_result import finish_match, build_result_embed


def player_id(player):
    if isinstance(player, dict):
        return str(player.get("id") or player.get("player_id") or "")
    return str(player or "")


def player_name(player):
    if isinstance(player, dict):
        return player.get("display_name") or player.get("name") or "Unknown"
    return str(player or "Not selected")


def find_player(match, reference):
    wanted = player_id(reference)

    for team in ("red", "blue"):
        for player in match.get(f"{team}_xi", []):
            if player_id(player) == wanted:
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

    batting = match.get("batting_team", "red")
    bowling = match.get("bowling_team", "blue")
    runs = int(match.get("runs", 0))
    wickets = int(match.get("wickets", 0))
    overs = int(match.get("overs_completed", 0))
    balls = int(match.get("balls_in_over", 0))

    embed = discord.Embed(
        title="🏏 Cricket Apex — Match Centre",
        description=(
            f"**{match.get(f'{batting}_name', batting.title())}** batting\n"
            f"vs **{match.get(f'{bowling}_name', bowling.title())}**"
        ),
        color=discord.Color.green(),
    )

    embed.add_field(name="Score", value=f"**{runs}/{wickets}**")
    embed.add_field(
        name="Overs",
        value=f"{overs}.{balls} / {match.get('overs', 20)}",
    )
    embed.add_field(name="Innings", value=str(match.get("innings", 1)))
    embed.add_field(name="Striker", value=player_name(match.get("striker")))
    embed.add_field(
        name="Non-striker",
        value=player_name(match.get("non_striker")),
    )
    embed.add_field(
        name="Bowler",
        value=player_name(match.get("current_bowler")),
    )
    embed.add_field(
        name="Status",
        value=str(match.get("status", "unknown")).replace("_", " ").title(),
        inline=False,
    )

    if match.get("target") is not None:
        embed.add_field(name="Target", value=str(match["target"]))

    if match.get("last_delivery"):
        embed.add_field(
            name="Last delivery",
            value=str(match["last_delivery"])[:1024],
            inline=False,
        )

    return embed


class DeliverySelect(discord.ui.Select):
    def __init__(self, match_id, kind):
        self.match_id = str(match_id)
        self.kind = kind

        match = load_matches().get(self.match_id, {})
        bowler = find_player(match, match.get("current_bowler")) or {}

        if kind == "variation":
            values = bowling_variations(bowler)
            placeholder = "Bowling captain: choose variation"
        elif kind == "shot":
            values = BATTING_SHOTS
            placeholder = "Batting captain: choose shot"
        elif kind == "intent":
            values = BATTING_INTENTS
            placeholder = "Batting captain: choose intent"
        else:
            values = BOWLING_LENGTHS
            placeholder = "Bowling captain: choose length"

        options = [
            discord.SelectOption(label=str(value)[:100], value=str(value))
            for value in list(values)[:25]
        ]

        if not options:
            options = [
                discord.SelectOption(label="Unavailable", value="Unavailable")
            ]

        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"apex:{self.match_id}:{kind}",
        )

    async def callback(self, interaction: discord.Interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match or match.get("status") != "live":
            return await interaction.response.send_message(
                "The match is not ready for a delivery.",
                ephemeral=True,
            )

        batting = match.get("batting_team", "red")
        bowling = match.get("bowling_team", "blue")
        captain_team = (
            batting if self.kind in ("shot", "intent") else bowling
        )
        captain = str(match.get(f"{captain_team}_captain") or "")

        if str(interaction.user.id) != captain:
            return await interaction.response.send_message(
                f"Only the {captain_team} captain can change this option.",
                ephemeral=True,
            )

        match.setdefault("delivery_choices", {})[self.kind] = self.values[0]
        save_matches(matches)

        await interaction.response.send_message(
            f"Selected **{self.values[0]}**.",
            ephemeral=True,
        )


class SubmitDeliveryButton(discord.ui.Button):
    def __init__(self, match_id):
        self.match_id = str(match_id)
        super().__init__(
            label="Deliver Ball",
            style=discord.ButtonStyle.success,
            custom_id=f"apex:{self.match_id}:deliver",
        )

    async def callback(self, interaction: discord.Interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match or match.get("status") != "live":
            return await interaction.response.send_message(
                "The match is not live.",
                ephemeral=True,
            )

        batting = match.get("batting_team", "red")
        bowling = match.get("bowling_team", "blue")
        allowed = {
            str(match.get(f"{batting}_captain") or ""),
            str(match.get(f"{bowling}_captain") or ""),
        }

        if str(interaction.user.id) not in allowed:
            return await interaction.response.send_message(
                "Only a team captain can submit a delivery.",
                ephemeral=True,
            )

        choices = match.get("delivery_choices", {})
        required = ("variation", "shot", "intent", "length")
        missing = [key for key in required if not choices.get(key)]

        if missing:
            return await interaction.response.send_message(
                "Choose all options first: " + ", ".join(missing),
                ephemeral=True,
            )

        batter_ref = match.get("striker")
        bowler_ref = match.get("current_bowler")
        batter = find_player(match, batter_ref)
        bowler = find_player(match, bowler_ref)

        if not batter or not bowler:
            return await interaction.response.send_message(
                "The striker or bowler is missing. Check opening selection.",
                ephemeral=True,
            )

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
        wicket = bool(result.get("wicket"))
        legal = bool(result.get("legal", True))

        match["runs"] = int(match.get("runs", 0)) + runs

        extra_type = result.get("extra")
        if extra_type:
            extras = match.setdefault("extras", {})
            extras[extra_type] = int(extras.get(extra_type, 0)) + runs

        striker_id = player_id(batter_ref)
        faced = match.setdefault("batted_players", [])

        if striker_id and striker_id not in faced:
            faced.append(striker_id)

        if wicket:
            match["wickets"] = int(match.get("wickets", 0)) + 1
            dismissed = match.setdefault("dismissed_players", [])

            if striker_id not in [player_id(p) for p in dismissed]:
                dismissed.append(striker_id)

            match["dismissed_slot"] = "striker"
            match["striker"] = None

        # Count legal balls only.
        total_balls = (
            int(match.get("overs_completed", 0)) * 6
            + int(match.get("balls_in_over", 0))
        )

        if legal:
            total_balls += 1

        match["overs_completed"] = total_balls // 6
        match["balls_in_over"] = total_balls % 6

        # Rotate strike on odd runs, except when the striker was dismissed.
        if runs % 2 == 1 and not wicket:
            match["striker"], match["non_striker"] = (
                match.get("non_striker"),
                match.get("striker"),
            )

        over_finished = legal and total_balls > 0 and total_balls % 6 == 0

        if over_finished:
            match["striker"], match["non_striker"] = (
                match.get("non_striker"),
                match.get("striker"),
            )
            match["previous_bowler"] = bowler_ref

        match["last_delivery"] = result.get(
            "description", "Delivery complete."
        )
        match["delivery_choices"] = {}

        innings = int(match.get("innings", 1))
        target = match.get("target")
        all_out = int(match.get("wickets", 0)) >= 10
        overs_limit = int(match.get("overs", 20))
        innings_over = int(match.get("overs_completed", 0)) >= overs_limit

        # The chase ends immediately when the target is reached.
        chase_won = (
            innings == 2
            and target is not None
            and int(match["runs"]) >= int(target)
        )

        if chase_won:
            outcome = finish_match(match)
            match["status"] = "completed"

        elif all_out or innings_over:
            if innings == 1:
                outcome = finish_match(match)
                # Second innings needs its opening selections.
                match["status"] = "opening_selection"
            else:
                outcome = finish_match(match)
                match["status"] = "completed"

        elif wicket:
            match["status"] = "batter_selection"
            outcome = None

        elif over_finished:
            match["status"] = "bowler_selection"
            outcome = None

        else:
            match["status"] = "live"
            outcome = None

        save_matches(matches)

        if match["status"] == "completed":
            await interaction.response.edit_message(
                content="🏆 **Match completed!**",
                embed=build_result_embed(match),
                view=None,
            )
            return

        if match["status"] == "opening_selection":
            await interaction.response.edit_message(
                content="🏏 **First innings complete!**",
                embed=build_result_embed(match),
                view=None,
            )

            from views.opening_selection import send_opening_selection

            await send_opening_selection(interaction.channel, self.match_id)
            return

        await interaction.response.edit_message(
            embed=build_match_embed(self.match_id),
            view=MatchView(self.match_id) if match["status"] == "live" else None,
        )

        await interaction.followup.send(
            f"🏏 {match['last_delivery']}",
            ephemeral=False,
        )

        if match["status"] == "batter_selection":
            from views.next_batter import send_next_batter_selection
            await send_next_batter_selection(
                interaction.channel, self.match_id
            )

        elif match["status"] == "bowler_selection":
            from views.over_selection import send_next_bowler_selection
            await send_next_bowler_selection(
                interaction.channel, self.match_id
            )


class MatchView(discord.ui.View):
    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.match_id = str(match_id)

        self.add_item(DeliverySelect(self.match_id, "variation"))
        self.add_item(DeliverySelect(self.match_id, "shot"))
        self.add_item(DeliverySelect(self.match_id, "intent"))
        self.add_item(DeliverySelect(self.match_id, "length"))
        self.add_item(SubmitDeliveryButton(self.match_id))
