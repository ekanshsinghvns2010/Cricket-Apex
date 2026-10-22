
import discord

from utils.match_utils import load_matches, save_matches
from utils.match_engine import (
    bowling_variations,
    BOWLING_LENGTHS,
    BATTING_SHOTS,
    BATTING_INTENTS,
    delivery_result,
)


def get_match(match_id):
    return load_matches().get(str(match_id))


def overs_text(balls):
    balls = max(0, int(balls or 0))
    return f"{balls // 6}.{balls % 6}"


def team_label(team):
    return "🔴 Red Team" if team == "red" else "🔵 Blue Team"


def build_match_embed(match_id):
    match = get_match(match_id)

    if not match:
        return discord.Embed(
            title="Match not found",
            color=discord.Color.red(),
        )

    runs = int(match.get("runs", 0))
    wickets = int(match.get("wickets", 0))
    balls = int(match.get("balls", 0))
    overs_limit = int(
        match.get("overs_limit", match.get("overs", 5))
    )
    target = match.get("target")

    embed = discord.Embed(
        title="🏏 CRICKET APEX • LIVE MATCH",
        description=(
            f"**{team_label(match.get('batting_team', 'red'))} batting**\n"
            f"## {runs}/{wickets}\n"
            f"Overs: **{overs_text(balls)}/{overs_limit}.0**\n"
            f"Target: **{target if target is not None else '—'}**"
        ),
        color=discord.Color.gold(),
    )

    batters = match.get("batters", [])

    if batters:
        lines = []

        for index, player in enumerate(batters[:2]):
            marker = "🏏" if index == 0 else "　"
            name = player.get(
                "display_name",
                player.get("name", "Batter"),
            )
            lines.append(
                f"{marker} **{name}** — "
                f"{player.get('runs', 0)} "
                f"({player.get('balls', 0)})"
            )

        embed.add_field(
            name="BATTERS",
            value="\n".join(lines),
            inline=False,
        )

    bowler = match.get("current_bowler")

    if bowler:
        embed.add_field(
            name="CURRENT BOWLER",
            value=(
                f"**{bowler.get('display_name', bowler.get('name', 'Bowler'))}**\n"
                f"{bowler.get('wickets', 0)} wickets • "
                f"{bowler.get('runs_conceded', 0)} runs"
            ),
            inline=False,
        )

    recent = match.get("recent_balls", [])

    embed.add_field(
        name="RECENT BALLS",
        value="  ".join(
            f"`{ball.get('display', ball.get('runs', 0))}`"
            for ball in recent[-12:]
        ) or "Waiting for first delivery...",
        inline=False,
    )

    commentary = match.get("last_commentary")

    if commentary:
        embed.add_field(
            name="COMMENTARY",
            value=commentary[:1024],
            inline=False,
        )

    if match.get("result"):
        embed.add_field(
            name="MATCH STATUS",
            value=str(match["result"])[:1024],
            inline=False,
        )

    embed.set_footer(text=f"Match {match_id} • Cricket Apex")
    return embed


class MatchView(discord.ui.View):
    """Dynamic, stage-specific controls for a match delivery."""

    def __init__(self, match_id):
        super().__init__(timeout=300)
        self.match_id = str(match_id)

        match = get_match(self.match_id)

        if not match or match.get("status") != "live":
            return

        stage = match.get("interaction_stage", "variation")

        if stage == "variation":
            bowler = match.get("current_bowler") or {}
            options = bowling_variations(bowler)
            self.add_choice_buttons(
                "variation",
                options,
                discord.ButtonStyle.primary,
            )

        elif stage == "length":
            self.add_choice_buttons(
                "length",
                BOWLING_LENGTHS,
                discord.ButtonStyle.secondary,
            )

        elif stage == "shot":
            self.add_choice_buttons(
                "shot",
                BATTING_SHOTS,
                discord.ButtonStyle.success,
            )

        elif stage == "intent":
            self.add_choice_buttons(
                "intent",
                BATTING_INTENTS,
                discord.ButtonStyle.primary,
            )

    def add_choice_buttons(self, category, options, style):
        for index, value in enumerate(options):
            button = discord.ui.Button(
                label=value,
                style=style,
                row=index // 3,
            )

            async def callback(
                interaction,
                selected=value,
                selected_category=category,
            ):
                await self.choose(
                    interaction,
                    selected_category,
                    selected,
                )

            button.callback = callback
            self.add_item(button)

    def load(self):
        matches = load_matches()
        return matches, matches.get(self.match_id)

    def stage_text(self, match):
        if match.get("status") == "completed":
            return "🏁 **Innings finished.**"

        stage = match.get("interaction_stage", "variation")

        messages = {
            "variation": "⚡ **Bowler's turn — choose a bowling variation.**",
            "length": "🎯 **Choose the delivery length.**",
            "shot": "🏏 **Batter's turn — choose a shot.**",
            "intent": "🔥 **Choose your batting intent.**",
        }

        return messages.get(stage, "🏏 Preparing the next delivery...")

    async def choose(self, interaction, category, value):
        matches, match = self.load()

        if not match or match.get("status") != "live":
            await interaction.response.send_message(
                "This match is not live.",
                ephemeral=True,
            )
            return

        expected_stage = {
            "variation": "variation",
            "length": "length",
            "shot": "shot",
            "intent": "intent",
        }.get(category)

        if match.get("interaction_stage", "variation") != expected_stage:
            await interaction.response.send_message(
                "That choice is no longer active. Use the latest match buttons.",
                ephemeral=True,
            )
            return

        if category == "variation":
            bowler = match.get("current_bowler") or {}

            if value not in bowling_variations(bowler):
                await interaction.response.send_message(
                    "That variation is not available for this bowler.",
                    ephemeral=True,
                )
                return

            match["selected_variation"] = value
            match["interaction_stage"] = "length"

        elif category == "length":
            if value not in BOWLING_LENGTHS:
                await interaction.response.send_message(
                    "Invalid bowling length.",
                    ephemeral=True,
                )
                return

            match["selected_length"] = value
            match["interaction_stage"] = "shot"

        elif category == "shot":
            if value not in BATTING_SHOTS:
                await interaction.response.send_message(
                    "Invalid batting shot.",
                    ephemeral=True,
                )
                return

            match["selected_shot"] = value
            match["interaction_stage"] = "intent"

        elif category == "intent":
            if value not in BATTING_INTENTS:
                await interaction.response.send_message(
                    "Invalid batting intent.",
                    ephemeral=True,
                )
                return

            match["selected_intent"] = value
            self.resolve_ball(match)

            if match.get("status") == "live":
                match["interaction_stage"] = "variation"

        save_matches(matches)

        # Rebuild the view so only the current stage's buttons appear.
        new_view = MatchView(self.match_id)
        new_embed = build_match_embed(self.match_id)

        await interaction.response.edit_message(
            content=self.stage_text(match),
            embed=new_embed,
            view=new_view,
        )

    def resolve_ball(self, match):
        batters = match.setdefault("batters", [])
        bowler = match.get("current_bowler")

        # Temporary fallback until real card-based XI selection is connected.
        if not batters:
            batters.extend([
                {
                    "name": "Batter 1",
                    "display_name": "Batter 1",
                    "batting_ovr": 60,
                    "fitness": 80,
                    "runs": 0,
                    "balls": 0,
                    "team": match.get("batting_team"),
                },
                {
                    "name": "Batter 2",
                    "display_name": "Batter 2",
                    "batting_ovr": 60,
                    "fitness": 80,
                    "runs": 0,
                    "balls": 0,
                    "team": match.get("batting_team"),
                },
            ])

        if not bowler:
            bowler = {
                "name": "Bowler",
                "display_name": "Bowler",
                "bowling_ovr": 60,
                "fielding_ovr": 60,
                "fitness": 80,
                "wickets": 0,
                "runs_conceded": 0,
                "legal_balls": 0,
                "team": match.get("bowling_team"),
                "bowling_style": "Right Arm Fast",
            }
            match["current_bowler"] = bowler

        striker = batters[0]

        result = delivery_result(
            striker,
            bowler,
            match.get("selected_variation", "Seam"),
            match.get("selected_length", "Good length"),
            match.get("selected_shot", "Defensive block"),
            match.get("selected_intent", "Balanced"),
            match.get("pitch", "Normal"),
        )

        runs = int(result.get("runs", 0))
        extra = result.get("extra")
        wicket = bool(result.get("wicket"))
        legal = bool(result.get("legal"))

        match["runs"] = int(match.get("runs", 0)) + runs

        # In this prototype, a wide is one extra run and no-ball is
        # represented by one extra run from delivery_result().
        batter_runs = 0 if extra == "wide" else runs

        striker["runs"] = int(striker.get("runs", 0)) + batter_runs

        if legal:
            striker["balls"] = int(striker.get("balls", 0)) + 1
            match["balls"] = int(match.get("balls", 0)) + 1
            bowler["legal_balls"] = (
                int(bowler.get("legal_balls", 0)) + 1
            )

        bowler["runs_conceded"] = (
            int(bowler.get("runs_conceded", 0))
            + (0 if extra == "wide" else runs)
        )

        if wicket:
            match["wickets"] = int(match.get("wickets", 0)) + 1
            bowler["wickets"] = int(bowler.get("wickets", 0)) + 1

        if extra == "wide":
            display = "WD"
        elif extra == "no-ball":
            display = "NB"
        elif wicket:
            display = "W"
        else:
            display = str(runs)

        recent = match.setdefault("recent_balls", [])
        recent.append({
            "runs": runs,
            "display": display,
            "wicket": wicket,
            "extra": extra,
            "description": result.get("description", ""),
        })
        match["recent_balls"] = recent[-24:]
        match["last_commentary"] = result.get(
            "description",
            "Delivery completed.",
        )

        # Rotate strike for odd batter runs.
        if batter_runs % 2 == 1 and len(batters) >= 2:
            batters[0], batters[1] = batters[1], batters[0]

        # Swap ends after a completed over.
        if legal and match["balls"] % 6 == 0 and len(batters) >= 2:
            batters[0], batters[1] = batters[1], batters[0]

        overs_limit = int(
            match.get("overs_limit", match.get("overs", 5))
        )

        if (
            int(match.get("wickets", 0)) >= 10
            or int(match.get("balls", 0)) >= overs_limit * 6
        ):
            match["status"] = "completed"
            match["state"] = "MATCH_END"
            match["result"] = (
                f"Innings ended: "
                f"{match['runs']}/{match['wickets']} "
                f"({overs_text(match['balls'])} overs)."
            )
