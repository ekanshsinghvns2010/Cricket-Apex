
import asyncio
import logging

import discord

from utils.match_utils import load_matches, save_matches

logger = logging.getLogger(__name__)
_ACTIVE_COUNTDOWNS = set()


async def start_countdown(message, match_id):
    from views.matches_lobby import MatchLobbyView, build_lobby_embed
    from views.toss_view import build_toss_embed
    from views.player_selection import (
        PlayerSelectionView,
        build_selection_embed,
    )

    match_id = str(match_id)

    if match_id in _ACTIVE_COUNTDOWNS:
        logger.info("Countdown already running for match %s", match_id)
        return

    _ACTIVE_COUNTDOWNS.add(match_id)

    try:
        matches = load_matches()
        match = matches.get(match_id)

        if not match:
            logger.error("Match %s not found", match_id)
            return

        blocked_statuses = {
            "starting",
            "toss",
            "selecting",
            "xi_confirmation",
            "opening_selection",
            "live",
            "completed",
            "cancelled",
        }

        if match.get("status") in blocked_statuses:
            logger.info(
                "Cannot start countdown for %s; status=%s",
                match_id,
                match.get("status"),
            )
            return

        guild = message.guild
        if guild is None:
            logger.error("Match %s has no guild", match_id)
            return

        # Validate team capacity using humans AND bots.
        team_size = int(match.get("team_size", 1))

        if team_size < 1:
            await message.channel.send(
                "❌ Match cannot start: team size must be at least 1."
            )
            return

        for team in ("red", "blue"):
            members = match.get(f"{team}_team") or []
            bots = match.get(f"{team}_bots") or []
            captain = match.get(f"{team}_captain")

            total_players = len(members) + len(bots)

            if total_players == 0:
                await message.channel.send(
                    f"❌ Match cannot start: the {team} team is empty."
                )
                return

            # A team with human players needs a captain.
            # A bot-only team does not need a Discord-user captain.
            if members and not captain:
                await message.channel.send(
                    f"❌ Match cannot start: the {team} team needs a captain."
                )
                return

            if total_players != team_size:
                await message.channel.send(
                    f"❌ Match cannot start: the {team} team has "
                    f"{total_players}/{team_size} players "
                    "(including bots)."
                )
                return

        match["status"] = "starting"
        match["state"] = "COUNTDOWN"
        save_matches(matches)

        lobby_view = MatchLobbyView(match_id)
        for child in lobby_view.children:
            child.disabled = True

        # Countdown
        for seconds in (5, 4, 3, 2, 1):
            matches = load_matches()
            match = matches.get(match_id)

            if not match or match.get("status") != "starting":
                return

            embed = await build_lobby_embed(guild, match_id)
            status_text = f"⏳ Match starts in **{seconds}**..."

            status_index = next(
                (
                    i
                    for i, field in enumerate(embed.fields)
                    if field.name == "Status"
                ),
                None,
            )

            if status_index is None:
                embed.add_field(
                    name="Status",
                    value=status_text,
                    inline=False,
                )
            else:
                embed.set_field_at(
                    status_index,
                    name="Status",
                    value=status_text,
                    inline=False,
                )

            await message.edit(embed=embed, view=lobby_view)
            await asyncio.sleep(1)

        matches = load_matches()
        match = matches.get(match_id)

        if not match or match.get("status") != "starting":
            return

        # Toss
        match["state"] = "TOSS"
        save_matches(matches)

        toss_embed = await build_toss_embed(guild, match_id)

        matches = load_matches()
        match = matches.get(match_id)

        if not match:
            return

        if not match.get("batting_team") or not match.get("bowling_team"):
            logger.error("Toss failed to set teams for match %s", match_id)

            await message.edit(
                content=(
                    "❌ Toss failed. Please cancel and create "
                    "the match again."
                ),
                embed=toss_embed,
                view=None,
            )
            return

        match["status"] = "toss"
        match["state"] = "TOSS"
        save_matches(matches)

        await message.edit(
            content=None,
            embed=toss_embed,
            view=None,
        )

        logger.info("Toss displayed for match %s", match_id)

        await asyncio.sleep(4)

        matches = load_matches()
        match = matches.get(match_id)

        if not match:
            return

        # Confirm that both sides still have players, including bots.
        for team in ("red", "blue"):
            members = match.get(f"{team}_team") or []
            bots = match.get(f"{team}_bots") or []

            if not members and not bots:
                logger.error(
                    "The %s team is empty after toss for match %s",
                    team,
                    match_id,
                )
                await message.channel.send(
                    f"❌ The {team} team is empty. Match setup stopped."
                )
                return

        # Prepare player selection.
        match["status"] = "selecting"
        match["state"] = "PLAYER_SELECTION"
        match["card_selections"] = []
        match["red_xi"] = []
        match["blue_xi"] = []
        match["xi_confirmed"] = {
            "red": False,
            "blue": False,
        }

        # Initialize match scoring state.
        match.setdefault("innings", 1)
        match.setdefault("runs", 0)
        match.setdefault("wickets", 0)
        match.setdefault("overs_completed", 0)
        match.setdefault("balls_in_over", 0)
        match.setdefault("target", None)

        match["overs_limit"] = int(match.get("overs", 5))
        match["batters"] = []
        match["recent_balls"] = []

        match.pop("current_bowler", None)
        match.pop("striker", None)
        match.pop("non_striker", None)

        save_matches(matches)

        red_embed = build_selection_embed(match, "red")
        blue_embed = build_selection_embed(match, "blue")

        await message.edit(
            content=(
                "🏏 **Toss complete! Player selection is open.**\n"
                "Each human teammate should select their assigned "
                "player cards. Captains can confirm the XI once the "
                "required cards are selected.\n\n"
                "🤖 Bot players count toward lobby capacity, but "
                "bot-team XI selection may need additional setup."
            ),
            embed=red_embed,
            view=PlayerSelectionView(match_id, "red"),
        )

        await message.channel.send(
            embed=blue_embed,
            view=PlayerSelectionView(match_id, "blue"),
        )

        logger.info(
            "Match %s moved to player selection",
            match_id,
        )

    except discord.NotFound:
        logger.exception(
            "Lobby message not found for match %s",
            match_id,
        )
        raise

    except discord.Forbidden:
        logger.exception(
            "Missing permission to update match %s",
            match_id,
        )
        raise

    except Exception:
        logger.exception(
            "Countdown or match transition failed for %s",
            match_id,
        )
        raise

    finally:
        _ACTIVE_COUNTDOWNS.discard(match_id)
