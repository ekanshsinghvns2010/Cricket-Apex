
import json
import discord

from database import connect_db
from utils.match_utils import load_matches, save_matches


def get_owned_cards(user_id):
    """Return player cards actually owned by this user."""
    conn = connect_db()
    try:
        user = conn.execute(
            "SELECT cards FROM users WHERE user_id = ?",
            (str(user_id),),
        ).fetchone()

        if not user:
            return []

        try:
            card_ids = json.loads(user["cards"] or "[]")
        except (json.JSONDecodeError, TypeError):
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
                (str(card_id),),
            ).fetchone()

            if player:
                players.append(dict(player))

        return players
    finally:
        conn.close()


def contribution_counts(team_size):
    """Split 11 required cards as evenly as possible."""
    team_size = int(team_size)
    if not 1 <= team_size <= 11:
        raise ValueError("Team size must be between 1 and 11.")

    base, extra = divmod(11, team_size)
    return [
        base + (1 if index < extra else 0)
        for index in range(team_size)
    ]


def get_team(match, team):
    return match.get(f"{team}_team", [])


def get_captain(match, team):
    return str(match.get(f"{team}_captain") or "")


def selected_xi(match, team):
    return match.setdefault(f"{team}_xi", [])


def team_selection_complete(match, team):
    """Check that every teammate submitted their assigned cards."""
    members = [str(x) for x in get_team(match, team)]
    if not members:
        return False

    counts = contribution_counts(match["team_size"])
    selections = match.get("card_selections", [])

    for index, member_id in enumerate(members):
        selection = next(
            (
                item for item in selections
                if item.get("user_id") == member_id
                and item.get("team") == team
            ),
            None,
        )
        if not selection or len(selection.get("cards", [])) != counts[index]:
            return False

    xi = selected_xi(match, team)
    ids = [str(player.get("id")) for player in xi if isinstance(player, dict)]
    return len(xi) == 11 and len(ids) == 11 and len(set(ids)) == 11


def build_selection_embed(match, team):
    members = get_team(match, team)
    counts = contribution_counts(match["team_size"])
    selections = match.get("card_selections", [])
    lines = []

    for index, member_id in enumerate(members):
        selection = next(
            (
                item for item in selections
                if item.get("user_id") == str(member_id)
                and item.get("team") == team
            ),
            None,
        )
        amount = len(selection.get("cards", [])) if selection else 0
        lines.append(
            f"**{index + 1}.** <@{member_id}> — "
            f"{amount}/{counts[index]} cards"
        )

    xi = selected_xi(match, team)
    lines.extend(["", f"**Selected squad: {len(xi)}/11**"])

    for index, player in enumerate(xi, 1):
        lines.append(
            f"{index}. {player.get('display_name') or player.get('name', 'Player')} "
            f"({player.get('role', 'Player')})"
        )

    embed = discord.Embed(
        title=f"🏏 {team.title()} Team — Player Selection",
        description="\n".join(lines)[:4000],
        color=discord.Color.red() if team == "red" else discord.Color.blue(),
    )
    captain = get_captain(match, team)
    embed.add_field(
        name="Captain",
        value=f"<@{captain}>" if captain else "Not assigned",
        inline=True,
    )
    embed.add_field(name="Squad", value=f"{len(xi)}/11", inline=True)
    embed.set_footer(
        text="Each teammate must submit their assigned number of unique cards."
    )
    return embed


async def post_xi_confirmation(channel, match_id):
    """Post both captain confirmation messages once both XIs are complete."""
    from views.xi_confirmation import send_xi_confirmation

    matches = load_matches()
    match = matches.get(str(match_id))
    if not match:
        return

    if not (
        team_selection_complete(match, "red")
        and team_selection_complete(match, "blue")
    ):
        return

    # Avoid duplicate confirmation messages if callbacks arrive together.
    if match.get("xi_confirmation_posted"):
        return

    match["status"] = "xi_confirmation"
    match["state"] = "XI_CONFIRMATION"
    match["xi_confirmation_posted"] = True
    match["xi_confirmed"] = {"red": False, "blue": False}
    save_matches(matches)

    try:
        await send_xi_confirmation(channel, match_id, "red")
        await send_xi_confirmation(channel, match_id, "blue")
        await channel.send(
            "✅ Both squads are complete. Each captain must confirm their XI."
        )
    except Exception:
        # Allow retry if posting fails.
        matches = load_matches()
        match = matches.get(str(match_id))
        if match:
            match["xi_confirmation_posted"] = False
            save_matches(matches)
        raise


class CardPicker(discord.ui.View):
    def __init__(self, match_id, team, user_id):
        super().__init__(timeout=300)
        self.match_id = str(match_id)
        self.team = team
        self.user_id = str(user_id)

        matches = load_matches()
        match = matches.get(self.match_id)
        if not match or team not in ("red", "blue"):
            return

        members = [str(x) for x in get_team(match, team)]
        if self.user_id not in members:
            return

        counts = contribution_counts(match["team_size"])
        self.required = counts[members.index(self.user_id)]

        existing = next(
            (
                item.get("cards", [])
                for item in match.get("card_selections", [])
                if item.get("user_id") == self.user_id
                and item.get("team") == team
            ),
            [],
        )

        owned = get_owned_cards(self.user_id)
        options = []

        for player in owned[:25]:
            card_id = str(player["id"])
            label = (
                player.get("display_name")
                or player.get("name")
                or card_id
            )[:100]
            options.append(
                discord.SelectOption(
                    label=label,
                    value=card_id,
                    description=(
                        f"{player.get('role') or 'Player'} · "
                        f"OVR {player.get('ovr') or 0}"
                    )[:100],
                    default=card_id in existing,
                )
            )

        self.card_select = None
        if len(options) >= self.required:
            self.card_select = discord.ui.Select(
                placeholder=f"Choose exactly {self.required} cards",
                min_values=self.required,
                max_values=self.required,
                options=options,
            )
            self.card_select.callback = self.save_selection
            self.add_item(self.card_select)

        button = discord.ui.Button(
            label="Save my cards",
            style=discord.ButtonStyle.success,
        )
        button.callback = self.save_button
        self.add_item(button)

    async def save_selection(self, interaction):
        await interaction.response.defer(ephemeral=True)

    async def save_button(self, interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message(
                "This picker belongs to another player.",
                ephemeral=True,
            )
            return

        if self.card_select is None:
            await interaction.response.send_message(
                f"You need at least {self.required} available owned cards.",
                ephemeral=True,
            )
            return

        chosen_ids = list(self.card_select.values)
        if len(chosen_ids) != self.required:
            await interaction.response.send_message(
                f"Select exactly {self.required} cards first.",
                ephemeral=True,
            )
            return

        owned = {
            str(player["id"]): player
            for player in get_owned_cards(self.user_id)
        }
        if any(card_id not in owned for card_id in chosen_ids):
            await interaction.response.send_message(
                "One or more cards are no longer owned by you.",
                ephemeral=True,
            )
            return

        matches = load_matches()
        match = matches.get(self.match_id)
        if not match or match.get("status") != "selecting":
            await interaction.response.send_message(
                "Card selection is closed for this match.",
                ephemeral=True,
            )
            return

        if self.user_id not in [
            str(x) for x in get_team(match, self.team)
        ]:
            await interaction.response.send_message(
                "You are no longer on this team.",
                ephemeral=True,
            )
            return

        selections = match.setdefault("card_selections", [])

        # Remove this teammate's old selection before checking conflicts.
        selections[:] = [
            item for item in selections
            if not (
                item.get("user_id") == self.user_id
                and item.get("team") == self.team
            )
        ]

        assigned_ids = {
            str(card_id)
            for item in selections
            if item.get("team") == self.team
            for card_id in item.get("cards", [])
        }

        if len(set(chosen_ids)) != len(chosen_ids):
            await interaction.response.send_message(
                "You cannot select the same card twice.",
                ephemeral=True,
            )
            return

        if any(card_id in assigned_ids for card_id in chosen_ids):
            await interaction.response.send_message(
                "A selected card is already assigned to a teammate. "
                "Choose different cards.",
                ephemeral=True,
            )
            return

        selections.append({
            "user_id": self.user_id,
            "team": self.team,
            "cards": chosen_ids,
        })

        xi = []
        for item in selections:
            if item.get("team") != self.team:
                continue
            for card_id in item.get("cards", []):
                player = owned.get(str(card_id))
                if player:
                    xi.append(player)

        match[f"{self.team}_xi"] = xi
        save_matches(matches)

        await interaction.response.send_message(
            f"Saved {len(chosen_ids)} cards. "
            f"Your team currently has {len(xi)}/11 players.",
            ephemeral=True,
        )

        if (
            team_selection_complete(match, self.team)
            and team_selection_complete(match, "red")
            and team_selection_complete(match, "blue")
        ):
            await post_xi_confirmation(interaction.channel, self.match_id)


class PlayerSelectionView(discord.ui.View):
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
            ),
        )
        button.callback = self.open_picker
        self.add_item(button)

    async def open_picker(self, interaction):
        matches = load_matches()
        match = matches.get(self.match_id)

        if not match:
            await interaction.response.send_message(
                "Match not found.",
                ephemeral=True,
            )
            return

        if match.get("status") != "selecting":
            await interaction.response.send_message(
                "Player selection is not open.",
                ephemeral=True,
            )
            return

        if str(interaction.user.id) not in [
            str(x) for x in get_team(match, self.team)
        ]:
            await interaction.response.send_message(
                "You are not on this team.",
                ephemeral=True,
            )
            return

        picker = CardPicker(
            self.match_id,
            self.team,
            interaction.user.id,
        )

        if picker.card_select is None:
            await interaction.response.send_message(
                "You do not have enough available owned cards for your allocation.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=build_selection_embed(match, self.team),
            view=picker,
            ephemeral=True,
        )
