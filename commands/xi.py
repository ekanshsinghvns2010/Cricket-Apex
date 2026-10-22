
import json
import discord
from discord.ext import commands

from database import connect_db
from commands.xi import get_owned_players, calculate_team_ovr


def load_user_xi(user_id):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT playing_xi FROM users WHERE user_id=?",
            (str(user_id),),
        )
        row = cursor.fetchone()

        if not row or not row["playing_xi"]:
            return []

        try:
            data = json.loads(row["playing_xi"])
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    finally:
        conn.close()


def save_user_xi(user_id, player_ids):
    conn = connect_db()
    try:
        conn.execute(
            "UPDATE users SET playing_xi=? WHERE user_id=?",
            (json.dumps(player_ids), str(user_id)),
        )
        conn.commit()
    finally:
        conn.close()


class XIBuilder(discord.ui.View):
    def __init__(self, owner_id, players):
        super().__init__(timeout=300)
        self.owner_id = int(owner_id)
        self.players = players
        self.selected = []
        self.page = 0
        self.page_size = 20
        self.refresh()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Only the person who opened this XI builder can use it.",
                ephemeral=True,
            )
            return False
        return True

    def refresh(self):
        self.clear_items()

        page_count = max(
            1,
            (len(self.players) + self.page_size - 1) // self.page_size,
        )
        self.page = max(0, min(self.page, page_count - 1))

        start = self.page * self.page_size
        end = start + self.page_size

        options = []

        for player in self.players[start:end]:
            player_id = str(player["id"])
            label = (
                f"{player.get('display_name') or player.get('name') or player_id}"
                f" | OVR {player.get('ovr', 0)}"
            )[:100]

            options.append(
                discord.SelectOption(
                    label=label,
                    value=player_id,
                    description=(
                        f"{player.get('role', 'Unknown role')} • "
                        f"{player.get('rarity', 'Common')}"
                    )[:100],
                    default=player_id in self.selected,
                )
            )

        if options:
            picker = discord.ui.Select(
                placeholder="Select players for your Playing XI",
                min_values=0,
                max_values=min(11, len(options)),
                options=options,
                custom_id="xi_builder_player_select",
            )
            picker.callback = self.select_players
            self.add_item(picker)

        previous = discord.ui.Button(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            disabled=self.page == 0,
            row=1,
        )
        previous.callback = self.previous_page
        self.add_item(previous)

        next_button = discord.ui.Button(
            label="Next",
            style=discord.ButtonStyle.secondary,
            disabled=self.page >= page_count - 1,
            row=1,
        )
        next_button.callback = self.next_page
        self.add_item(next_button)

        save_button = discord.ui.Button(
            label="Save Playing XI",
            style=discord.ButtonStyle.success,
            emoji="💾",
            row=2,
        )
        save_button.callback = self.save_xi
        self.add_item(save_button)

        clear_button = discord.ui.Button(
            label="Clear Selection",
            style=discord.ButtonStyle.danger,
            row=2,
        )
        clear_button.callback = self.clear_selection
        self.add_item(clear_button)

    async def select_players(self, interaction):
        values = list(interaction.data.get("values", []))
        current_page_ids = {
            str(p["id"])
            for p in self.players[
                self.page * self.page_size:
                (self.page + 1) * self.page_size
            ]
        }

        self.selected = [
            player_id
            for player_id in self.selected
            if player_id not in current_page_ids
        ]

        self.selected.extend(values)

        if len(self.selected) > 11:
            self.selected = self.selected[:11]

        self.refresh()

        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def previous_page(self, interaction):
        self.page -= 1
        self.refresh()
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def next_page(self, interaction):
        self.page += 1
        self.refresh()
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def clear_selection(self, interaction):
        self.selected = []
        self.refresh()
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def save_xi(self, interaction):
        if len(self.selected) != 11:
            await interaction.response.send_message(
                f"Select exactly 11 players first. "
                f"Currently selected: {len(self.selected)}/11.",
                ephemeral=True,
            )
            return

        owned_ids = {str(p["id"]) for p in self.players}

        if any(player_id not in owned_ids for player_id in self.selected):
            await interaction.response.send_message(
                "Your selection contains a card you do not own. Reopen the XI builder.",
                ephemeral=True,
            )
            return

        save_user_xi(self.owner_id, self.selected)

        self.stop()

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="✅ **Playing XI saved!** Your selected batting order is preserved.",
            embed=self.build_embed(),
            view=self,
        )

    def build_embed(self):
        by_id = {str(p["id"]): p for p in self.players}
        selected_players = [
            by_id[player_id]
            for player_id in self.selected
            if player_id in by_id
        ]

        lines = []

        for index, player in enumerate(selected_players, start=1):
            name = player.get("display_name") or player.get("name") or "Unknown"
            lines.append(
                f"**{index}.** {name} — "
                f"OVR **{player.get('ovr', 0)}** "
                f"({player.get('role', '?')})"
            )

        embed = discord.Embed(
            title="🏏 Playing XI Builder",
            description=(
                "Select 11 cards from your collection. "
                "The order shown here is your batting order.\n\n"
                "**Selected players**\n"
                + ("\n".join(lines) if lines else "No players selected.")
            ),
            color=discord.Color.green(),
        )

        embed.add_field(
            name="Selection",
            value=f"{len(self.selected)}/11 players",
            inline=True,
        )
        embed.add_field(
            name="Team OVR",
            value=str(calculate_team_ovr(selected_players)),
            inline=True,
        )
        embed.set_footer(
            text=f"Cards owned: {len(self.players)} • Page {self.page + 1}"
        )

        return embed


def setup_xi(bot):
    @bot.command(name="xi")
    async def xi(ctx):
        players = get_owned_players(ctx.author.id)

        if len(players) < 11:
            await ctx.send(
                f"❌ You need at least 11 owned player cards to create a "
                f"Playing XI. You currently own {len(players)}.\n"
                "Get more players and try `g!xi` again."
            )
            return

        saved_ids = load_user_xi(ctx.author.id)
        owned_by_id = {str(p["id"]): p for p in players}

        # Restore the saved batting order, ignoring cards no longer owned.
        ordered = [
            owned_by_id[player_id]
            for player_id in saved_ids
            if player_id in owned_by_id
        ]

        # Fill the remaining list with cards not already in the saved XI.
        used = {str(p["id"]) for p in ordered}
        remaining = [
            p for p in players
            if str(p["id"]) not in used
        ]

        view = XIBuilder(ctx.author.id, ordered + remaining)

        # Preselect the existing saved XI in its saved order.
        view.selected = [
            str(p["id"]) for p in ordered[:11]
        ]
        view.refresh()

        await ctx.send(
            embed=view.build_embed(),
            view=view,
        )
