import asyncio
import logging

import discord

from utils.match_utils import load_matches, save_matches

logger = logging.getLogger(__name__)

_ACTIVE_COUNTDOWNS = set()


async def start_countdown(message, match_id):
    from views.matches_lobby import (
        MatchLobbyView,
        build_lobby_embed
    )
    from views.toss_view import build_toss_embed
    from views.match_view import build_match_embed

    match_id = str(match_id)

    if match_id in _ACTIVE_COUNTDOWNS:
        logger.info(
            "Countdown already running for match %s",
            match_id
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
            "toss", "live", "completed", "cancelled"
        ):
            logger.info(
                "Cannot start countdown for %s; status=%s",
                match_id,
                match.get("status")
            )
            return

        guild = message.guild

        if guild is None:
            logger.error(
                "Lobby message has no guild for match %s",
                match_id
            )
            return

        match["status"] = "starting"
        match["state"] = "COUNTDOWN"
        save_matches(matches)

        lobby_view = MatchLobbyView(match_id)

        for child in lobby_view.children:
            child.disabled = True

        for seconds in (5, 4, 3, 2, 1):
            matches = load_matches()
            match = matches.get(match_id)

            if match is None:
                logger.error(
                    "Match %s disappeared during countdown",
                    match_id
                )
                return

            embed = await build_lobby_embed(
                guild,
                match_id
            )

            status_index = next(
                (
                    index
                    for index, field in enumerate(embed.fields)
                    if field.name == "Status"
                ),
                None
            )

            status_text = (
                f"⏳ Match starts in **{seconds}**..."
            )

            if status_index is None:
                embed.add_field(
                    name="Status",
                    value=status_text,
                    inline=False
                )
            else:
                embed.set_field_at(
                    status_index,
                    name="Status",
                    value=status_text,
                    inline=False
                )

            await message.edit(
                embed=embed,
                view=lobby_view
            )

            logger.info(
                "Match %s countdown: %s",
                match_id,
                seconds
            )

            await asyncio.sleep(1)

        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error(
                "Match %s disappeared before toss",
                match_id
            )
            return

        match["state"] = "TOSS"
        save_matches(matches)

        toss_embed = await build_toss_embed(
            guild,
            match_id
        )

        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error(
                "Match %s disappeared while preparing toss",
                match_id
            )
            return

        match["status"] = "toss"
        match["state"] = "TOSS"
        save_matches(matches)

        await message.edit(
            embed=toss_embed,
            view=None
        )

        logger.info(
            "Toss displayed for match %s",
            match_id
        )

        # Leave the toss result visible briefly.
        await asyncio.sleep(4)

        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error(
                "Match %s disappeared after toss",
                match_id
            )
            return

        # Initialize the match automatically after the toss.
        match.setdefault("innings", 1)
        match.setdefault("runs", 0)
        match.setdefault("wickets", 0)
        match.setdefault("overs_completed", 0)
        match.setdefault("balls", 0)
        match.setdefault("target", None)

        if not match.get("batting_team") or not match.get("bowling_team"):
            logger.error(
                "Toss did not initialize batting and bowling teams "
                "for match %s",
                match_id
            )
            return

        match["status"] = "live"
        match["state"] = "MATCH"
        save_matches(matches)

        match_embed = build_match_embed(match_id)

        await message.edit(
            embed=match_embed,
            view=None
        )

        logger.info(
            "Match %s initialized and marked live",
            match_id
        )

    except discord.NotFound:
        logger.exception(
            "Lobby message not found for match %s",
            match_id
        )
        raise

    except discord.Forbidden:
        logger.exception(
            "Missing permission to update match %s",
            match_id
        )
        raise

    except Exception:
        logger.exception(
            "Countdown or match transition failed for %s",
            match_id
        )
        raise

    finally:
        _ACTIVE_COUNTDOWNS.discard(match_id)