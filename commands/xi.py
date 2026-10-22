
import json
import discord
from discord.ext import commands

from database import connect_db


ROLE_ORDER = {"BAT": 1, "WK": 2, "AR": 3, "BOWL": 4}

COUNTRY_FLAGS = {
    "India": "🇮🇳",
    "Pakistan": "🇵🇰",
    "Australia": "🇦🇺",
    "England": "🏴",
    "South Africa": "🇿🇦",
    "Bangladesh": "🇧🇩",
    "Afghanistan": "🇦🇫",
    "Sri Lanka": "🇱🇰",
    "New Zealand": "🇳🇿",
    "West Indies": "🏝️",
}

RARITY_EMOJIS = {
    "Common": "⚪",
    "Rare": "🔵",
    "Epic": "🟣",
    "Legendary": "🟡",
    "Icon": "🔴",
}

BOWLING_EMOJIS = {
    "Right Arm Fast": "⚡",
    "Left Arm Fast": "⚡",
    "Right Arm Medium": "🎯",
    "Left Arm Medium": "🎯",
    "Off Spin": "🌀",
    "Offspin": "🌀",
    "Leg Spin": "🌪️",
    "Legspin": "🌪️",
    "Left Arm Orthodox": "🌀",
    "Chinaman": "🌪️",
}

CARD_EMOJI = "🏏"
SUCCESS_EMOJI = "✅"


def get_owned_players(user_id):
    """Fetch all player cards owned by a user."""
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cards FROM users WHERE user_id = ?",
            (str(user_id),),
        )
        row = cursor.fetchone()

        if not row or not row["cards"]:
            return []

        try:
            card_ids = json.loads(row["cards"])
        except (json.JSONDecodeError, TypeError):
            return []

        if not isinstance(card_ids, list):
            return []

        players = []
        seen = set()

        for card_id in card_ids:
            card_id = str(card_id)
            if card_id in seen:
                continue
            seen.add(card_id)

            cursor.execute(
                "SELECT * FROM players WHERE id = ?",
                (card_id,),
            )
            player = cursor.fetchone()

            if player:
                players.append(dict(player))

        players.sort(
            key=lambda p: (
                ROLE_ORDER.get(p.get("role", ""), 99),
                -int(p.get("ovr") or 0),
                str(p.get("display_name") or p.get("name") or ""),
            )
        )
        return players
    finally:
        conn.close()


def load_user_xi(user_id):
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT playing_xi FROM users WHERE user_id = ?",
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
            "UPDATE users SET playing_xi = ? WHERE user_id = ?",
            (json.dumps(player_ids), str(user_id)),
        )
        conn.commit()
    finally:
        conn.close()


def calculate_team_ovr(players):
    if not players:
        return 0
    return round(
        sum(int(p.get("ovr") or 0) for p in players) / len(players)
    )


def get_flag(country):
    return COUNTRY_FLAGS.get(country, "🏳️")


def get_card_emoji(rarity):
    return RARITY_EMOJIS.get(rarity, CARD_EMOJI)


def get_bowling_emoji(style):
    return BOWLING_EMOJIS.get(style, "🏏")


def format_player(player):
    name = str(
        player.get("display_name") or player.get("name") or "Unknown"
    )[:15]

    return (
        f"{get_flag(player.get('country', ''))} | "
        f"{get_card_emoji(player.get('rarity', ''))} | "
        f"**`{name:^15}`** | "
        f"`{int(player.get('ovr') or 0):>2}` | "
        f"`{int(player.get('batting_ovr') or 0):>2}` | "
        f"`{int(player.get('bowling_ovr') or 0):>2}` | "
        f"{get_bowling_emoji(player.get('bowling_style', ''))}"
    )


def build_personal_xi_embed(owner, players, selected_ids):
    selected_ids = [str(pid) for pid in selected_ids]
    by_id = {str(p["id"]): p for p in players}

    selected = [
        by_id[pid] for pid in selected_ids
        if pid in by_id
    ][:11]

    lines = [
        f"**{owner.display_name}** {CARD_EMOJI} "
        f"**OVR: {calculate_team_ovr(selected)}**",
        "",
        "`country`  |  `card`  |  `player`  |  `ovr`  |  `bat`  |  `bowl`",
        "",
    ]

    sections = [
        ("BAT", "__**BATTERS 🏏**__"),
        ("WK", "__**WICKET KEEPERS 🧤**__"),
        ("AR", "__**ALL-ROUNDERS 🏏**__"),
        ("BOWL", "__**BOWLERS 🏏**__"),
    ]

    for role, heading in sections:
        role_players = [p for p in selected if p.get("role") == role]
        if not role_players:
            continue

        lines.append(heading)
        lines.extend(format_player(p) for p in role_players)
        lines.append("")

    if len(selected) == 11:
        lines.append(f"{SUCCESS_EMOJI} XI is valid for match.")
    else:
        lines.append(f"Selected: **{len(selected)}/11 players**.")

    embed = discord.Embed(
        description="\n".join(lines),
        color=discord.Color.green(),
    )
    embed.set_author(
        name=f"{owner.display_name}'s Personal XI",
        icon_url=owner.display_avatar.url,
    )
    embed.add_field(name="Cards Owned", value=str(len(players)), inline=True)
    embed.add_field(name="Playing XI", value=f"{len(selected)}/11", inline=True)
    embed.add_field(
        name="Substitutes",
        value=str(max(0, len(players) - len(selected))),
        inline=True,
    )
    return embed


def build_substitutes_embed(owner, players, selected_ids):
    selected_ids = {str(pid) for pid in selected_ids}
    substitutes = [
        p for p in players if str(p["id"]) not in selected_ids
    ]

    lines = [
        f"**{owner.display_name}** — Substitute Players",
        "",
        "`country`  |  `card`  |  `player`  |  `ovr`  |  `bat`  |  `bowl`",
        "",
    ]

    sections = [
        ("BAT", "__**BATTERS 🏏**__"),
        ("WK", "__**WICKET KEEPERS 🧤**__"),
        ("AR", "__**ALL-ROUNDERS 🏏**__"),
        ("BOWL", "__**BOWLERS 🏏**__"),
    ]

    for role, heading in sections:
        role_players = [p for p in substitutes if p.get("role") == role]
        if role_players:
            lines.append(heading)
            lines.extend(format_player(p) for p in role_players)
            lines.append("")

    if not substitutes:
        lines.append("You don't have any substitute players.")

    embed = discord.Embed(
        description="\n".join(lines),
        color=discord.Color.blurple(),
    )
    embed.set_author(
        name=f"{owner.display_name}'s Squad",
        icon_url=owner.display_avatar.url,
    )
    embed.set_footer(text=f"{len(substitutes)} substitute player(s)")
    return embed


class PersonalXIView(discord.ui.View):
    def __init__(self, owner, players):
        super().__init__(timeout=300)
        self.owner = owner
        self.owner_id = owner.id
        self.players = players
        self.page = 0
        self.page_size = 25

        owned = {str(p["id"]) for p in players}
        self.selected = [
            str(pid) for pid in load_user_xi(owner.id)
            if str(pid) in owned
        ][:11]

        self.section = "xi"
        self.refresh()

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Only the owner can use this Personal XI.",
                ephemeral=True,
            )
            return False
        return True

    def current_embed(self):
        if self.section == "subs":
            return build_substitutes_embed(
                self.owner, self.players, self.selected
            )
        return build_personal_xi_embed(
            self.owner, self.players, self.selected
        )

    def refresh(self):
        self.clear_items()

        # Two section buttons.
        playing_button = discord.ui.Button(
            label="Playing XI",
            emoji="🏏",
            style=discord.ButtonStyle.success,
            row=0,
        )
        playing_button.callback = self.show_xi
        self.add_item(playing_button)

        substitutes_button = discord.ui.Button(
            label="Substitutes",
            emoji="🪑",
            style=discord.ButtonStyle.primary,
            row=0,
        )
        substitutes_button.callback = self.show_substitutes
        self.add_item(substitutes_button)

        page_count = max(
            1,
            (len(self.players) + self.page_size - 1) // self.page_size,
        )
        self.page = max(0, min(self.page, page_count - 1))

        page_players = self.players[
            self.page * self.page_size:
            (self.page + 1) * self.page_size
        ]

        if page_players:
            options = []
            for player in page_players:
                pid = str(player["id"])
                name = player.get("display_name") or player.get("name") or pid

                options.append(
                    discord.SelectOption(
                        label=f"{name} | OVR {player.get('ovr', 0)}"[:100],
                        value=pid,
                        description=(
                            f"{player.get('role', '?')} • "
                            f"{player.get('country', 'Unknown')} • "
                            f"{player.get('rarity', 'Common')}"
                        )[:100],
                        default=pid in self.selected,
                    )
                )

            picker = discord.ui.Select(
                placeholder="Choose cards for your preferred XI",
                min_values=0,
                max_values=min(11, len(options)),
                options=options,
                row=1,
            )
            picker.callback = self.select_players
            self.add_item(picker)

        previous = discord.ui.Button(
            label="Previous",
            style=discord.ButtonStyle.secondary,
            disabled=self.page == 0,
            row=2,
        )
        previous.callback = self.previous_page
        self.add_item(previous)

        next_button = discord.ui.Button(
            label="Next",
            style=discord.ButtonStyle.secondary,
            disabled=self.page >= page_count - 1,
            row=2,
        )
        next_button.callback = self.next_page
        self.add_item(next_button)

        save_button = discord.ui.Button(
            label="Save Personal XI",
            style=discord.ButtonStyle.success,
            row=2,
        )
        save_button.callback = self.save_xi
        self.add_item(save_button)

    async def show_xi(self, interaction):
        self.section = "xi"
        await interaction.response.edit_message(
            embed=self.current_embed(),
            view=self,
        )

    async def show_substitutes(self, interaction):
        self.section = "subs"
        await interaction.response.edit_message(
            embed=self.current_embed(),
            view=self,
        )

    async def select_players(self, interaction):
        values = list(interaction.data.get("values", []))
        current_page_ids = {
            str(p["id"])
            for p in self.players[
                self.page * self.page_size:
                (self.page + 1) * self.page_size
            ]
        }

        # Keep selections from other pages.
        self.selected = [
            pid for pid in self.selected if pid not in current_page_ids
        ]

        for pid in values:
            if pid not in self.selected and len(self.selected) < 11:
                self.selected.append(pid)

        self.section = "xi"
        self.refresh()

        await interaction.response.edit_message(
            embed=self.current_embed(),
            view=self,
        )

    async def previous_page(self, interaction):
        self.page -= 1
        self.refresh()
        await interaction.response.edit_message(
            embed=self.current_embed(),
            view=self,
        )

    async def next_page(self, interaction):
        self.page += 1
        self.refresh()
        await interaction.response.edit_message(
            embed=self.current_embed(),
            view=self,
        )

    async def save_xi(self, interaction):
        if len(self.selected) != 11:
            await interaction.response.send_message(
                f"Select exactly 11 cards first "
                f"({len(self.selected)}/11).",
                ephemeral=True,
            )
            return

        owned_ids = {str(p["id"]) for p in self.players}
        if (
            len(set(self.selected)) != 11
            or any(pid not in owned_ids for pid in self.selected)
        ):
            await interaction.response.send_message(
                "❌ Invalid selection. Select 11 different cards you own.",
                ephemeral=True,
            )
            return

        save_user_xi(self.owner_id, self.selected)
        self.section = "xi"

        await interaction.response.edit_message(
            content="✅ Your Personal XI has been saved.",
            embed=self.current_embed(),
            view=self,
        )


def setup_xi(bot):
    @bot.command(name="xi")
    async def xi(ctx):
        players = get_owned_players(ctx.author.id)

        if not players:
            await ctx.send(
                "❌ You don't own any player cards yet. "
                "Buy players using `g!buy` first."
            )
            return

        view = PersonalXIView(ctx.author, players)

        await ctx.send(
            embed=view.current_embed(),
            view=view,
        )
