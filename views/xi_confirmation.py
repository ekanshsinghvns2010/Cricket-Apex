
import discord
from discord.ui import View, Button

from utils.match_utils import load_matches, save_matches


def get_team_name(match, team):
    return match.get(f"{team}_name", team.title())


def get_xi(match, team):
    xi = match.get(f"{team}_xi", [])
    return xi if isinstance(xi, list) else []


def get_captain(match, team):
    return str(match.get(f"{team}_captain") or "")


def player_id(player):
    if isinstance(player, dict):
        return str(player.get("id", ""))
    return str(player)


def build_xi_embed(match, team):
    xi = get_xi(match, team)
    confirmed = match.get("xi_confirmed", {}).get(team, False)

    embed = discord.Embed(
        title=f"🏏 {get_team_name(match, team)} — Playing XI",
        description=(
            "Review the selected player cards. "
            "Only the team captain can confirm this XI."
        ),
        color=(
            discord.Color.green()
            if confirmed
            else discord.Color.blurple()
        ),
    )

    for index, player in enumerate(xi, 1):
        if isinstance(player, dict):
            name = player.get("display_name") or player.get("name", "Unknown")
            role = player.get("role", "Player")
            ovr = player.get("ovr", "?")
        else:
            name, role, ovr = str(player), "Player", "?"

        embed.add_field(
            name=f"{index}. {name}",
            value=f"Role: {role} · OVR: {ovr}",
            inline=False,
        )

    if not xi:
        embed.description += "\n\nNo players have been selected yet."

    embed.add_field(
        name="Squad",
        value=f"{len(xi)}/11",
        inline=True,
    )
    embed.add_field(
        name="Captain confirmation",
        value="✅ Confirmed" if confirmed else "⏳ Pending",
        inline=True,
    )
    return embed


class XIConfirmationView(View):
    def __init__(self, match_id: str, team: str):
        super().__init__(timeout=None)
        if team not in ("red", "blue"):
            raise ValueError("team must be 'red' or 'blue'")

        self.match_id = str(match_id)
        self.team = team

    async def interaction_check(self, interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "This match no longer exists.",
                ephemeral=True,
            )
            return False

        if str(interaction.user.id) != get_captain(match, self.team):
            await interaction.response.send_message(
                "Only your team's captain can confirm its XI.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="Confirm Playing XI",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="cricket_apex:confirm_xi",
    )
    async def confirm_xi(self, interaction, button: Button):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "This match no longer exists.",
                ephemeral=True,
            )
            return

        if match.get("status") not in {
            "selecting",
            "xi_confirmation",
        }:
            await interaction.response.send_message(
                "XI confirmation is not open.",
                ephemeral=True,
            )
            return

        xi = get_xi(match, self.team)

        if len(xi) != 11:
            await interaction.response.send_message(
                f"Your XI must contain exactly 11 players; "
                f"currently selected: {len(xi)}.",
                ephemeral=True,
            )
            return

        ids = [player_id(player) for player in xi]

        if any(not value for value in ids) or len(set(ids)) != 11:
            await interaction.response.send_message(
                "Your XI must contain 11 unique player cards.",
                ephemeral=True,
            )
            return

        # Confirm only after validating the selected squad.
        confirmed = match.setdefault(
            "xi_confirmed",
            {"red": False, "blue": False},
        )
        confirmed[self.team] = True

        both_confirmed = (
            confirmed.get("red", False)
            and confirmed.get("blue", False)
        )

        if both_confirmed:
            match["status"] = "opening_selection"
            match["state"] = "OPENING_SELECTION"
            match["interaction_stage"] = "opening_selection"
        else:
            match["status"] = "xi_confirmation"

        save_matches(matches)

        await interaction.response.edit_message(
            embed=build_xi_embed(match, self.team),
            view=self,
        )

        if both_confirmed:
            # Open a shared message with the opening batter/bowler menus.
            from views.opening_selection import (
                send_opening_selection,
            )

            channel = interaction.channel
            if channel is not None:
                await send_opening_selection(channel, self.match_id)
        else:
            await interaction.followup.send(
                f"{self.team.title()} XI confirmed. Waiting for the other captain.",
                ephemeral=True,
            )


async def send_xi_confirmation(channel, match_id, team):
    matches = load_matches()
    match = matches.get(str(match_id))

    if not match:
        raise ValueError(f"Match {match_id} was not found.")

    if team not in ("red", "blue"):
        raise ValueError("team must be 'red' or 'blue'")

    return await channel.send(
        embed=build_xi_embed(match, team),
        view=XIConfirmationView(str(match_id), team),
    )
