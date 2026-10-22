import asyncio
import logging

import discord

from utils.match_utils import load_matches, save_matches

logger = logging.getLogger(__name__)

# Prevent duplicate countdowns for the same match.
_ACTIVE_COUNTDOWNS = set()


async def start_countdown(message, match_id):
    from views.matches_lobby import MatchLobbyView, build_lobby_embed
    from views.toss_view import build_toss_embed

    match_id = str(match_id)

    if match_id in _ACTIVE_COUNTDOWNS:
        logger.info("Countdown already running for match %s", match_id)
        return

    _ACTIVE_COUNTDOWNS.add(match_id)

    try:
        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error("Match %s was not found", match_id)
            return

        if match.get("status") in (
            "toss", "live", "completed", "cancelled"
        ):
            logger.info(
                "Match %s cannot start countdown; status=%s",
                match_id,
                match.get("status")
            )
            return

        guild = message.guild
        if guild is None:
            logger.error("Lobby message has no guild")
            return

        match["status"] = "starting"
        save_matches(matches)

        view = MatchLobbyView(match_id)
        for child in view.children:
            child.disabled = True

        for seconds in (5, 4, 3, 2, 1):
            matches = load_matches()
            if match_id not in matches:
                logger.error("Match %s disappeared during countdown", match_id)
                return

            embed = await build_lobby_embed(guild, match_id)

            status_index = next(
                (
                    i for i, field in enumerate(embed.fields)
                    if field.name == "Status"
                ),
                None
            )

            status_text = f"⏳ Match starts in **{seconds}**..."

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

            await message.edit(embed=embed, view=view)
            logger.info("Match %s countdown: %s", match_id, seconds)

            await asyncio.sleep(1)

        matches = load_matches()
        if match_id not in matches:
            logger.error("Match %s disappeared before toss", match_id)
            return

        # Generate the toss result.
        toss_embed = await build_toss_embed(guild, match_id)

        matches = load_matches()
        match = matches.get(match_id)
        if match is None:
            logger.error("Match %s disappeared while preparing toss", match_id)
            return

        match["status"] = "toss"
        save_matches(matches)

        # Replace the lobby with the toss result.
        await message.edit(embed=toss_embed, view=None)

        logger.info("Match %s toss displayed successfully", match_id)

    except discord.NotFound:
        logger.exception("Lobby message not found for match %s", match_id)
        raise

    except discord.Forbidden:
        logger.exception("Missing permission to edit match %s lobby", match_id)
        raise

    except Exception:
        logger.exception("Countdown failed for match %s", match_id)
        raise

    finally:
        _ACTIVE_COUNTDOWNS.discard(match_id)