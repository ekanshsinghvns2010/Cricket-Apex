
import json
import discord

from database import connect_db
from utils.match_utils import load_matches, save_matches


def get_owned_cards(user_id):
    """Return the actual player cards owned by a user."""
    conn = connect_db()
    try:
        user = conn.execute(
            "SELECT cards FROM users WHERE user_id = ?",
            (str(user_id),)
        ).fetchone()

        if not user:
            return []

        try:
            card_ids = json.loads(user["cards"] or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

        if not card_ids:
            return []

        players = []
        for card_id in card_ids:
            player = conn.execute(
                """
                SELECT id, name, display_name, role,
                       batting_ovr, bowling_ovr, fielding_ovr,
                       batting_style, bowling_style, fitness, ovr
                FROM players
                WHERE id = ?
                """,
                (str(card_id),)
            ).fetchone()

            if player:
                players.append(dict(player))

        return players
    finally:
        conn.close()


def contribution_counts(team_size):
    """Distribute 11 cards fairly across the human team."""
    base, extra = divmod(11, int(team_size))
    return [
        base + (1 if i < extra else 0)
        for i in range(int(team_size))
    ]


def get_team(match, team):
    return match.get(f"{team}_team", [])


def get_captain(match, team):
    return str(match.get(f"{team}_captain") or "")


def selected_xi(match, team):
    return match.setdefault(f"{team}_xi", [])


def build_selection_embed(match, team):
    members = get_team(match, team)
    captain = get_captain(match, team)
    counts = contribution_counts(match["team_size"])

    lines = [
        f"**{i + 1}.** <@{user_id}> — "
        f"{len(next((x['cards'] for x in match.get('card_selections', [])
                    if x['user_id'] == str(user_id)), []))}/{counts[i]} cards"
        for i, user_id in enumerate(members)
    ]

    xi = selected_xi(match, team)
    lines.append("")
    lines.append(f"**Squad cards selected: {len(xi)}/11**")

    for index, player in enumerate(xi, 1):
        lines.append(
            f"{index}. {player.get('display_name') or player.get('name', 'Player')} "
            f"({player.get('role', 'Player')})"
        )

    embed = discord.Embed(
        title=f"🏏 {team.upper()} TEAM — PLAYER SELECTION",
        description="\n".join(lines)[:4000],
        color=discord.Color.red() if team == "red" else discord.Color.blue()
    )
    embed.add_field(
        name="Captain",
        value=f"<@{captain}>" if captain else "Not assigned",
        inline=True
    )
    embed.add_field(
        name="Squad",
        value=f"{len(xi)}/11",
        inline=True
    )
    embed.set_footer(
        text="Each teammate must select their assigned number of cards."
    )
    return embed


class CardPicker(discord.ui.View):
    """A teammate chooses owned cards for their team's squad."""

    def __init__(self, match_id, team, user_id):
        super().__init__(timeout=300)
        self.match_id = str(match_id)
        self.team = team
        self.user_id = str(user_id)

        matches = load_matches()
        match = matches.get(self.match_id)
        if not match:
            return

        members = get_team(match, team)
        if self.user_id not in [str(x) for x in members]:
            return

        counts = contribution_counts(match["team_size"])
        member_index = [str(x) for x in members].index(self.user_id)
        self.required = counts[member_index]

        existing = next(
            (
                item["cards"]
                for item in match.get("card_selections", [])
                if item["user_id"] == self.user_id
                and item["team"] == team
            ),
            []
        )
        self.existing = existing

        owned = get_owned_cards(self.user_id)
        options = []

        for player in owned[:25]:
            label = (
                player.get("display_name")
                or player.get("name")
                or str(player["id"])
            )[:100]
            role = str(player.get("role") or "Player")
            rating = player.get("ovr") or 0

            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(player["id"]),
                    description=f"{role} • OVR {rating}"[:100],
                    default=str(player["id"]) in existing
                )
            )

        if options:
            self.card_select = discord.ui.Select(
                placeholder=f"Choose {self.required} player card(s)",
                min_values=self.required,
                max_values=self.required,
                options=options
            )
            self.card_select.callback = self.save_selection
            self.add_item(self.card_select)

        save_button = discord.ui.Button(
            label="Save my cards",
            style=discord.ButtonStyle.success
        )
        save_button.callback = self.save_button
        self.add_item(save_button)

    async def save_selection(self, interaction):
        await interaction.response.defer(ephemeral=True)

    async def save_button(self, interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "This card picker belongs to another player.",
                ephemeral=True
            )
            return

        if not hasattr(self, "card_select"):
            await interaction.response.send_message(
                "You don't have any available player cards.",
                ephemeral=True
            )
            return

        chosen_ids = list(self.card_select.values)

        if len(chosen_ids) != self.required:
            await interaction.response.send_message(
                f"Select exactly {self.required} cards.",
                ephemeral=True
            )
            return

        # Verify all selected IDs are still owned.
        owned = {
            str(player["id"]): player
            for player in get_owned_cards(self.user_id)
        }

        if any(card_id not in owned for card_id in chosen_ids):
            await interaction.response.send_message(
                "One or more selected cards are no longer owned by you.",
                ephemeral=True
            )
            return

        matches = load_matches()
        match = matches.get(self.match_id)

        if not match or match.get("status") not in ("toss", "selecting"):
            await interaction.response.send_message(
                "This match is not accepting card selections.",
                ephemeral=True
            )
            return

        if self.user_id not in [
            str(x) for x in get_team(match, self.team)
        ]:
            await interaction.response.send_message(
                "You are no longer on this team.",
                ephemeral=True
            )
            return

        selections = match.setdefault("card_selections", [])

        # Replace this teammate's previous selection.
        selections[:] = [
            item for item in selections
            if not (
                item["user_id"] == self.user_id
                and item["team"] == self.team
            )
        ]

        # Prevent duplicate player IDs within the same team.
        other_team_cards = {
            str(card["id"])
            for item in selections
            if item["team"] == self.team
            for card in item.get("cards", [])
        }

        if any(card_id in other_team_cards for card_id in chosen_ids):
            await interaction.response.send_message(
                "A selected card is already assigned to a teammate. "
                "Choose different cards.",
                ephemeral=True
            )
            return

        selections.append({
            "user_id": self.user_id,
            "team": self.team,
            "cards": chosen_ids
        })

        # Rebuild the team's XI from all teammate selections.
        xi = []
        for item in selections:
            if item["team"] != self.team:
                continue
            for card_id in item["cards"]:
                player = owned.get(str(card_id))
                if player:
                    xi.append(player)

        match[f"{self.team}_xi"] = xi
        save_matches(matches)

        await interaction.response.send_message(
            f"Saved {len(chosen_ids)} card(s). "
            f"Your team has selected {len(xi)}/11 cards.",
            ephemeral=True
        )


class PlayerSelectionView(discord.ui.View):
    """Team members open their own card picker."""

    def __init__(self, match_id, team):
        super().__init__(timeout=600)
        self.match_id = str(match_id)
        self.team = team

        button = discord.ui.Button(
            label=f"Choose {team.title()} Team Cards",
            style=(
                discord.ButtonStyle.danger
                if team == "red"
                else discord.ButtonStyle.primary
            )
        )
        button.callback = self.open_picker
        self.add_item(button)

    async def open_picker(self, interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "Match not found.",
                ephemeral=True
            )
            return

        if str(interaction.user.id) not in [
            str(x) for x in get_team(match, self.team)
        ]:
            await interaction.response.send_message(
                "You are not on this team.",
                ephemeral=True
            )
            return

        picker = CardPicker(
            self.match_id,
            self.team,
            interaction.user.id
        )

        if not any(isinstance(item, discord.ui.Select) for item in picker.children):
            await interaction.response.send_message(
                "You need enough owned cards to make your selection.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            embed=build_selection_embed(match, self.team),
            view=picker,
            ephemeral=True
        )
