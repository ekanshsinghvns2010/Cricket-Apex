
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


def build_next_batter_embed(match):
    batting = match.get("batting_team", "red")
    name = match.get(f"{batting}_name", batting.title())

    embed = discord.Embed(
        title="🏏 Choose the Next Batter",
        description=(
            f"**Batting team:** {name}\n"
            f"**Score:** {match.get('runs', 0)}/"
            f"{match.get('wickets', 0)}\n\n"
            "The batting captain must choose a player who has not "
            "already batted and is not dismissed."
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


def available_batters(match):
    batting = match.get("batting_team", "red")
    xi = get_xi(match, batting)

    dismissed = dismissed_ids(match)
    used = {str(p) for p in match.get("batted_players", [])}

    for slot in ("striker", "non_striker"):
        current = player_id(match.get(slot))
        if current:
            used.add(current)

    return [
        player for player in xi
        if player_id(player)
        and player_id(player) not in dismissed
        and player_id(player) not in used
    ]


class NextBatterSelect(Select):
    def __init__(self, match_id):
        self.match_id = str(match_id)

        match = load_matches().get(self.match_id, {})
        options = [
            discord.SelectOption(
                label=player_name(player)[:100],
                value=player_id(player),
            )
            for player in available_batters(match)[:25]
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
            disabled=not available_batters(match),
        )

    async def callback(self, interaction: discord.Interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            return await interaction.response.send_message(
                "Match not found.", ephemeral=True
            )

        if match.get("status") != "batter_selection":
            return await interaction.response.send_message(
                "A new batter is not required right now.", ephemeral=True
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
                "No eligible batter remains. Complete the innings.",
                ephemeral=True,
            )

        selected = next(
            (
                player for player in get_xi(match, batting)
                if player_id(player) == selected_id
            ),
            None,
        )

        if not selected or selected not in available_batters(match):
            return await interaction.response.send_message(
                "That batter is unavailable. Reopen the selection.",
                ephemeral=True,
            )

        slot = match.get("dismissed_slot", "striker")
        if slot not in ("striker", "non_striker"):
            slot = "striker"

        match[slot] = selected
        match.setdefault("batted_players", []).append(selected_id)
        match.pop("dismissed_slot", None)
        match["status"] = "live"
        match["interaction_stage"] = "variation"

        save_matches(matches)

        from views.match_view import MatchView, build_match_embed

        await interaction.response.edit_message(
            content=f"✅ **{player_name(selected)}** comes in to bat!",
            embed=build_next_batter_embed(match),
            view=None,
        )

        if interaction.channel:
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

    available = available_batters(match)

    if not available:
        # No incoming batter: end this innings using the same transition
        # logic as the delivery handler.
        from utils.innings_result import finish_match

        outcome = finish_match(match)
        save_matches(matches)

        if outcome.get("match_over"):
            from utils.innings_result import build_result_embed

            await channel.send(embed=build_result_embed(match))
        else:
            from views.opening_selection import send_opening_selection

            await channel.send(
                embed=discord.Embed(
                    title="🏏 Innings Break",
                    description=outcome.get("message", "Innings complete."),
                    color=discord.Color.blurple(),
                )
            )
            await send_opening_selection(channel, key)
        return

    await channel.send(
        embed=build_next_batter_embed(match),
        view=NextBatterView(key),
    )
