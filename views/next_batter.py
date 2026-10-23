
# views/next_batter.py

import discord
from discord.ui import Select, View

from utils.match_utils import load_matches, save_matches


def player_id(player):
    if isinstance(player, dict):
        return str(player.get("id") or player.get("player_id") or "")
    return str(player or "")


def player_name(player):
    if isinstance(player, dict):
        return player.get("display_name") or player.get("name") or "Unknown"
    return str(player or "Unknown")


def get_xi(match, team):
    xi = match.get(f"{team}_xi", [])
    return xi if isinstance(xi, list) else []


def dismissed_ids(match):
    return {
        player_id(player)
        for player in match.get("dismissed_players", [])
        if player_id(player)
    }


def available_batters(match):
    batting = match.get("batting_team", "red")
    xi = get_xi(match, batting)

    dismissed = dismissed_ids(match)
    used = {
        str(player)
        for player in match.get("batted_players", [])
    }

    for slot in ("striker", "non_striker"):
        current_id = player_id(match.get(slot))
        if current_id:
            used.add(current_id)

    return [
        player
        for player in xi
        if player_id(player)
        and player_id(player) not in dismissed
        and player_id(player) not in used
    ]


def build_next_batter_embed(match):
    batting = match.get("batting_team", "red")
    team_name = match.get(f"{batting}_name", batting.title())

    embed = discord.Embed(
        title="🏏 Choose the Next Batter",
        description=(
            f"**Batting team:** {team_name}\n"
            f"**Score:** {match.get('runs', 0)}/"
            f"{match.get('wickets', 0)}\n\n"
            "The batting captain must select an eligible player "
            "who has not already batted."
        ),
        color=discord.Color.orange(),
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

    return embed


class NextBatterSelect(Select):
    def __init__(self, match_id):
        self.match_id = str(match_id)

        match = load_matches().get(self.match_id, {})
        eligible = available_batters(match)

        options = [
            discord.SelectOption(
                label=player_name(player)[:100],
                value=player_id(player),
            )
            for player in eligible[:25]
        ]

        if not options:
            options = [
                discord.SelectOption(
                    label="No eligible batters",
                    value="none",
                )
            ]

        super().__init__(
            placeholder="Select incoming batter",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"apex:{self.match_id}:next_batter",
            disabled=not eligible,
        )

    async def callback(self, interaction: discord.Interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            return await interaction.response.send_message(
                "Match not found.",
                ephemeral=True,
            )

        if match.get("status") != "batter_selection":
            return await interaction.response.send_message(
                "A replacement batter is not required right now.",
                ephemeral=True,
            )

        batting = match.get("batting_team", "red")
        captain = str(match.get(f"{batting}_captain") or "")

        if str(interaction.user.id) != captain:
            return await interaction.response.send_message(
                "Only the batting captain can select the next batter.",
                ephemeral=True,
            )

        selected_id = str(self.values[0])

        if selected_id == "none":
            return await interaction.response.send_message(
                "No eligible batter remains.",
                ephemeral=True,
            )

        selected = next(
            (
                player
                for player in get_xi(match, batting)
                if player_id(player) == selected_id
            ),
            None,
        )

        if selected is None or selected not in available_batters(match):
            return await interaction.response.send_message(
                "That batter is no longer available. Please reopen selection.",
                ephemeral=True,
            )

        slot = match.get("dismissed_slot", "striker")

        if slot not in ("striker", "non_striker"):
            slot = "striker"

        match[slot] = selected

        batted = match.setdefault("batted_players", [])
        if selected_id not in [str(value) for value in batted]:
            batted.append(selected_id)

        match.pop("dismissed_slot", None)

        # A wicket may also have ended the over.
        # The bowler must be selected before another delivery.
        if match.pop("pending_bowler_selection", False):
            match["status"] = "bowler_selection"
            match["interaction_stage"] = "bowler_selection"
        else:
            match["status"] = "live"
            match["interaction_stage"] = "variation"

        save_matches(matches)

        await interaction.response.edit_message(
            content=f"✅ **{player_name(selected)}** comes in to bat!",
            embed=build_next_batter_embed(match),
            view=None,
        )

        if not interaction.channel:
            return

        if match["status"] == "bowler_selection":
            from views.over_selection import send_next_bowler_selection

            await send_next_bowler_selection(
                interaction.channel,
                self.match_id,
            )
        else:
            from views.match_view import MatchView, build_match_embed

            await interaction.channel.send(
                embed=build_match_embed(self.match_id),
                view=MatchView(self.match_id),
            )


class NextBatterView(View):
    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.add_item(NextBatterSelect(str(match_id)))


async def send_next_batter_selection(channel, match_id):
    key = str(match_id)
    matches = load_matches()
    match = matches.get(key)

    if not match:
        raise ValueError(f"Match {key} was not found.")

    if match.get("status") != "batter_selection":
        raise ValueError("Match is not waiting for a new batter.")

    eligible = available_batters(match)

    if not eligible:
        from utils.innings_result import finish_match, build_result_embed

        outcome = finish_match(match)
        save_matches(matches)

        await channel.send(embed=build_result_embed(match))

        if outcome.get("innings_break"):
            from views.opening_selection import send_opening_selection

            await send_opening_selection(channel, key)

        return

    return await channel.send(
        embed=build_next_batter_embed(match),
        view=NextBatterView(key),
    )
