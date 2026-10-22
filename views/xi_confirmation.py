
# views/xi_confirmation.py

import discord
from discord.ui import View, Button
from utils.match_utils import load_matches, save_matches


def get_team_name(match, team):
    return match.get(f"{team}_name", team.replace("_", " ").title())


def get_xi(match, team):
    xi = match.get(f"{team}_xi", [])
    return xi if isinstance(xi, list) else []


def get_captain(match, team):
    return str(match.get(f"{team}_captain", ""))


def build_xi_embed(match, team):
    xi = get_xi(match, team)
    confirmed = match.get("xi_confirmed", {})
    team_confirmed = confirmed.get(team, False)

    embed = discord.Embed(
        title=f"🏏 {get_team_name(match, team)} — Playing XI",
        description=(
            "Review your team's selected players.\n"
            "The captain must confirm the XI before play can begin."
        ),
        color=discord.Color.green() if team_confirmed else discord.Color.blurple(),
    )

    if xi:
        for index, player in enumerate(xi, start=1):
            if isinstance(player, dict):
                name = player.get("display_name") or player.get("name", "Unknown")
                role = player.get("role", "Player")
                ovr = player.get("ovr", "?")
                player_id = player.get("id", "?")
            else:
                name = str(player)
                role = "Player"
                ovr = "?"
                player_id = "?"

            embed.add_field(
                name=f"{index}. {name}",
                value=f"Role: {role} · OVR: {ovr} · ID: {player_id}",
                inline=False,
            )
    else:
        embed.add_field(
            name="No players selected",
            value="Select your team's 11 cards first.",
            inline=False,
        )

    embed.add_field(
        name="Confirmation",
        value="✅ Confirmed" if team_confirmed else "⏳ Awaiting captain",
        inline=False,
    )

    return embed


class XIConfirmationView(View):
    def __init__(self, match_id: str, team: str):
        super().__init__(timeout=None)
        self.match_id = str(match_id)
        self.team = team

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "This match no longer exists.", ephemeral=True
            )
            return False

        captain_id = get_captain(match, self.team)

        if str(interaction.user.id) != captain_id:
            await interaction.response.send_message(
                "Only your team's captain can confirm this XI.",
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
    async def confirm_xi(
        self,
        interaction: discord.Interaction,
        button: Button,
    ):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "This match no longer exists.", ephemeral=True
            )
            return

        status = str(match.get("status", "")).lower()
        if status not in {"selecting", "xi_confirmation", "toss"}:
            await interaction.response.send_message(
                "XI confirmation is not open right now.",
                ephemeral=True,
            )
            return

        xi = get_xi(match, self.team)

        if len(xi) != 11:
            await interaction.response.send_message(
                f"Your XI must contain exactly 11 players. Current count: {len(xi)}.",
                ephemeral=True,
            )
            return

        player_ids = [
            str(p.get("id"))
            for p in xi
            if isinstance(p, dict) and p.get("id") is not None
        ]

        if len(player_ids) != 11 or len(set(player_ids)) != 11:
            await interaction.response.send_message(
                "Your XI must contain 11 unique player cards.",
                ephemeral=True,
            )
            return

        match.setdefault("xi_confirmed", {})
        match["xi_confirmed"][self.team] = True

        if match.get("team1") and match.get("team2"):
            team1 = "team1"
            team2 = "team2"

            if (
                match["xi_confirmed"].get(team1, False)
                and match["xi_confirmed"].get(team2, False)
            ):
                match["status"] = "ready_to_play"
                match["interaction_stage"] = "opening_selection"
            else:
                match["status"] = "xi_confirmation"

        save_matches(matches)

        await interaction.response.edit_message(
            embed=build_xi_embed(match, self.team),
            view=self,
        )

        if match.get("status") == "ready_to_play":
            channel = interaction.channel
            if channel:
                await channel.send(
                    "✅ Both captains confirmed their Playing XIs! "
                    "Next: select the opening batters and opening bowler."
                )


async def send_xi_confirmation(
    channel: discord.abc.Messageable,
    match_id: str,
    team: str,
):
    matches = load_matches()
    match = matches.get(str(match_id))

    if not match:
        raise ValueError(f"Match {match_id} was not found.")

    embed = build_xi_embed(match, team)

    return await channel.send(
        embed=embed,
        view=XIConfirmationView(str(match_id), team),
    )
