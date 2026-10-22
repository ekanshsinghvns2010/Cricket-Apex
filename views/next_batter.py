
# views/next_batter.py

import discord

from utils.match_utils import load_matches, save_matches


def get_match(match_id: str):
    matches = load_matches()
    return matches, matches.get(str(match_id))


def get_team_xi(match: dict, team: str) -> list:
    """Return the confirmed XI for a team."""
    return match.get(f"{team}_xi", [])


def player_id(player) -> str:
    """Support XI entries stored as IDs or dictionaries."""
    if isinstance(player, dict):
        return str(player.get("id", player.get("player_id", "")))
    return str(player)


def player_name(player) -> str:
    if isinstance(player, dict):
        return str(
            player.get("display_name")
            or player.get("name")
            or player.get("id")
            or "Unknown player"
        )
    return str(player)


class NextBatterSelect(discord.ui.Select):
    def __init__(self, match_id: str, options: list):
        self.match_id = str(match_id)

        select_options = [
            discord.SelectOption(
                label=player_name(player)[:100],
                value=player_id(player),
            )
            for player in options[:25]
        ]

        super().__init__(
            placeholder="Choose the incoming batter",
            min_values=1,
            max_values=1,
            options=select_options,
        )

    async def callback(self, interaction: discord.Interaction):
        matches, match = get_match(self.match_id)

        if not match:
            await interaction.response.send_message(
                "This match could not be found.", ephemeral=True
            )
            return

        batting_team = str(match.get("batting_team", ""))
        captain_key = f"{batting_team}_captain"
        captain_id = str(match.get(captain_key, ""))

        if str(interaction.user.id) != captain_id:
            await interaction.response.send_message(
                "Only the batting captain can choose the next batter.",
                ephemeral=True,
            )
            return

        if match.get("status") != "batter_selection":
            await interaction.response.send_message(
                "The match isn't waiting for a new batter.",
                ephemeral=True,
            )
            return

        selected_id = str(self.values[0])
        xi = get_team_xi(match, batting_team)

        eligible_ids = {player_id(player) for player in xi}
        dismissed = {
            str(pid) for pid in match.get("dismissed_players", [])
        }

        striker = str(match.get("striker", ""))
        non_striker = str(match.get("non_striker", ""))

        if selected_id not in eligible_ids:
            await interaction.response.send_message(
                "That player isn't in your confirmed XI.",
                ephemeral=True,
            )
            return

        if selected_id in dismissed:
            await interaction.response.send_message(
                "That batter has already been dismissed.",
                ephemeral=True,
            )
            return

        if selected_id in {striker, non_striker}:
            await interaction.response.send_message(
                "That player is already at the crease.",
                ephemeral=True,
            )
            return

        selected_player = next(
            player for player in xi
            if player_id(player) == selected_id
        )

        # A wicket normally requires the incoming batter to take strike.
        match["striker"] = selected_id
        match["striker_name"] = player_name(selected_player)
        match["status"] = "live"
        match["interaction_stage"] = "variation"

        save_matches(matches)

        await interaction.response.edit_message(
            content=(
                f"🏏 **{player_name(selected_player)}** is coming in to bat.\n"
                "The match is ready to continue."
            ),
            view=None,
        )


class NextBatterView(discord.ui.View):
    def __init__(self, match_id: str, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.match_id = str(match_id)

        _, match = get_match(self.match_id)

        if not match:
            return

        batting_team = str(match.get("batting_team", ""))
        xi = get_team_xi(match, batting_team)

        dismissed = {
            str(pid) for pid in match.get("dismissed_players", [])
        }

        active = {
            str(match.get("striker", "")),
            str(match.get("non_striker", "")),
        }

        eligible = [
            player for player in xi
            if player_id(player)
            and player_id(player) not in dismissed
            and player_id(player) not in active
        ]

        if eligible:
            self.add_item(NextBatterSelect(self.match_id, eligible))

    async def interaction_check(
        self, interaction: discord.Interaction
    ) -> bool:
        _, match = get_match(self.match_id)

        if not match:
            await interaction.response.send_message(
                "This match could not be found.", ephemeral=True
            )
            return False

        batting_team = str(match.get("batting_team", ""))
        captain_id = str(match.get(f"{batting_team}_captain", ""))

        if str(interaction.user.id) != captain_id:
            await interaction.response.send_message(
                "Only the batting captain can use this selection.",
                ephemeral=True,
            )
            return False

        return True
