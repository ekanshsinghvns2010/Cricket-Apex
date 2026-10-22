
import asyncio
import logging

import discord

from utils.match_utils import load_matches, save_matches

logger = logging.getLogger(__name__)

_ACTIVE_COUNTDOWNS = set()


async def start_countdown(message, match_id):
    from views.matches_lobby import (
        MatchLobbyView,
        build_lobby_embed,
    )
    from views.toss_view import build_toss_embed
    from views.match_view import MatchView, build_match_embed

    match_id = str(match_id)

    if match_id in _ACTIVE_COUNTDOWNS:
        logger.info(
            "Countdown already running for match %s",
            match_id,
        )
        return

    _ACTIVE_COUNTDOWNS.add(match_id)

    try:
        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error("Match %s not found", match_id)
            return

        if match.get("status") in (
            "toss",
            "live",
            "completed",
            "cancelled",
        ):
            logger.info(
                "Cannot start countdown for %s; status=%s",
                match_id,
                match.get("status"),
            )
            return

        guild = message.guild

        if guild is None:
            logger.error(
                "Lobby message has no guild for match %s",
                match_id,
            )
            return

        match["status"] = "starting"
        match["state"] = "COUNTDOWN"
        save_matches(matches)

        lobby_view = MatchLobbyView(match_id)

        for child in lobby_view.children:
            child.disabled = True

        # Countdown: 5, 4, 3, 2, 1.
        for seconds in (5, 4, 3, 2, 1):
            matches = load_matches()
            match = matches.get(match_id)

            if match is None:
                logger.error(
                    "Match %s disappeared during countdown",
                    match_id,
                )
                return

            embed = await build_lobby_embed(guild, match_id)

            status_index = next(
                (
                    index
                    for index, field in enumerate(embed.fields)
                    if field.name == "Status"
                ),
                None,
            )

            status_text = f"⏳ Match starts in **{seconds}**..."

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

            await message.edit(
                embed=embed,
                view=lobby_view,
            )

            logger.info(
                "Match %s countdown: %s",
                match_id,
                seconds,
            )

            await asyncio.sleep(1)

        # Confirm the match still exists before tossing.
        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error(
                "Match %s disappeared before toss",
                match_id,
            )
            return

        match["state"] = "TOSS"
        save_matches(matches)

        toss_embed = await build_toss_embed(guild, match_id)

        # Reload because build_toss_embed updates the saved toss result.
        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error(
                "Match %s disappeared while preparing toss",
                match_id,
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

        # Keep the toss result visible briefly.
        await asyncio.sleep(4)

        # Reload the latest match data.
        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error(
                "Match %s disappeared after toss",
                match_id,
            )
            return

        if not match.get("batting_team") or not match.get("bowling_team"):
            logger.error(
                "Toss did not initialize batting and bowling teams "
                "for match %s",
                match_id,
            )
            return

        # Initialize the interactive match.
        match.setdefault("innings", 1)
        match.setdefault("runs", 0)
        match.setdefault("wickets", 0)
        match.setdefault("overs_completed", 0)
        match.setdefault("balls", 0)
        match.setdefault("target", None)
        match["overs_limit"] = int(match.get("overs", 5))
        match["interaction_stage"] = "variation"
        match.setdefault("batters", [])
        match.setdefault("recent_balls", [])

        # Temporary bowler until selected lineups are connected.
        if not match.get("current_bowler"):
            match["current_bowler"] = {
                "name": "Bowler",
                "display_name": "Bowler",
                "bowling_ovr": 60,
                "fitness": 80,
                "wickets": 0,
                "runs_conceded": 0,
                "legal_balls": 0,
                "team": match.get("bowling_team"),
                "bowling_style": "Right Arm Fast",
            }

        match["status"] = "live"
        match["state"] = "MATCH"
        save_matches(matches)

        match_embed = build_match_embed(match_id)
        match_view = MatchView(match_id)

        await message.edit(
            content="⚡ **Bowler's turn — choose a bowling variation.**",
            embed=match_embed,
            view=match_view,
        )

        logger.info(
            "Match %s initialized and marked live",
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
