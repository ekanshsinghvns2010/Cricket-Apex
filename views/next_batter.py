
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


def get_dismissed_ids(match):
    dismissed = match.get("dismissed_players", [])
    result = set()

    for player in dismissed:
        if isinstance(player, dict):
            result.add(player_id(player))
        else:
            result.add(str(player))

    return result


def build_next_batter_embed(match):
    batting_team = match.get("batting_team", "red")
    team_name = match.get(f"{batting_team}_name", batting_team.title())

    embed = discord.Embed(
        title="🏏 Choose the Next Batter",
        description=(
            f"**Batting team:** {team_name}\n"
            f"**Score:** {match.get('runs', 0)}/"
            f"{match.get('wickets', 0)}\n\n"
            "The batting captain must select a player who has not "
            "already batted and is not dismissed."
        ),
        color=discord.Color.orange(),
    )

    embed.add_field(
        name="Current striker",
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

        matches = load_matches()
        match = matches.get(self.match_id, {})
        batting_team = match.get("batting_team", "red")
        xi = get_xi(match, batting_team)

        dismissed = get_dismissed_ids(match)
        used = set(match.get("batted_players", []))

        for slot in ("striker", "non_striker"):
            current_id = player_id(match.get(slot))
            if current_id:
                used.add(current_id)

        available = [
            player for player in xi
            if player_id(player)
            and player_id(player) not in dismissed
            and player_id(player) not in used
        ]

        options = [
            discord.SelectOption(
                label=player_name(player)[:100],
                value=player_id(player),
            )
            for player in available[:25]
        ]

        # Discord requires at least one option in a select menu.
        if not options:
            options = [
                discord.SelectOption(
                    label="No eligible batters available",
                    value="none",
                )
            ]

        super().__init__(
            placeholder="Select the incoming batter",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"cricket_apex:next_batter:{self.match_id}",
            disabled=not available,
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

        if match.get("status") != "batter_selection":
            await interaction.response.send_message(
                "A new batter is not required right now.",
                ephemeral=True,
            )
            return

        batting_team = match.get("batting_team", "red")
        captain_id = str(match.get(f"{batting_team}_captain") or "")

        if str(interaction.user.id) != captain_id:
            await interaction.response.send_message(
                "Only the batting captain can select the next batter.",
                ephemeral=True,
            )
            return

        selected_id = str(self.values[0])

        if selected_id == "none":
            await interaction.response.send_message(
                "No eligible batters remain. The innings must be checked.",
                ephemeral=True,
            )
            return

        xi = get_xi(match, batting_team)
        selected = next(
            (
                player for player in xi
                if player_id(player) == selected_id
            ),
            None,
        )

        if selected is None:
            await interaction.response.send_message(
                "That player is not in your confirmed XI.",
                ephemeral=True,
            )
            return

        dismissed = get_dismissed_ids(match)
        used = set(match.get("batted_players", []))

        for slot in ("striker", "non_striker"):
            current_id = player_id(match.get(slot))
            if current_id:
                used.add(current_id)

        if selected_id in dismissed or selected_id in used:
            await interaction.response.send_message(
                "That player has already batted or been dismissed. "
                "Choose another player.",
                ephemeral=True,
            )
            return

        # The dismissed striker's slot is replaced by the new batter.
        # If the non-striker was dismissed, the delivery handler must
        # set dismissed_slot='non_striker' before opening this view.
        dismissed_slot = match.get("dismissed_slot", "striker")

        if dismissed_slot not in ("striker", "non_striker"):
            dismissed_slot = "striker"

        match[dismissed_slot] = selected
        match.setdefault("batted_players", []).append(selected_id)
        match.pop("dismissed_slot", None)
        match["status"] = "live"
        match["interaction_stage"] = "variation"

        save_matches(matches)

        await interaction.response.edit_message(
            content=f"✅ {player_name(selected)} is coming in to bat.",
            embed=build_next_batter_embed(match),
            view=None,
        )

        # Refresh the main match display when a channel is available.
        if interaction.channel:
            from views.match_view import MatchView, build_match_embed

            try:
                await interaction.channel.send(
                    embed=build_match_embed(self.match_id),
                    view=MatchView(self.match_id),
                )
            except (discord.HTTPException, ValueError):
                pass


class NextBatterView(View):
    def __init__(self, match_id):
        super().__init__(timeout=None)
        self.add_item(NextBatterSelect(str(match_id)))


async def send_next_batter_selection(channel, match_id):
    matches = load_matches()
    match = matches.get(str(match_id))

    if not match:
        raise ValueError(f"Match {match_id} was not found.")

    if match.get("status") != "batter_selection":
        raise ValueError("This match is not waiting for a new batter.")

    batting_team = match.get("batting_team", "red")
    xi = get_xi(match, batting_team)
    dismissed = get_dismissed_ids(match)
    used = set(match.get("batted_players", []))

    for slot in ("striker", "non_striker"):
        current_id = player_id(match.get(slot))
        if current_id:
            used.add(current_id)

    available = [
        player for player in xi
        if player_id(player)
        and player_id(player) not in dismissed
        and player_id(player) not in used
    ]

    # An all-out innings should be completed by the innings manager.
    if not available:
        match["status"] = "innings_break"
        match["interaction_stage"] = "innings_break"
        save_matches(matches)

        await channel.send(
            "🏏 No eligible batters remain. The innings manager "
            "must complete this innings."
        )
        return

    await channel.send(
        embed=build_next_batter_embed(match),
        view=NextBatterView(str(match_id)),
    )
