
import asyncio
import logging

import discord

from utils.match_utils import load_matches, save_matches

logger = logging.getLogger(__name__)


async def start_countdown(message, match_id):
    from views.matches_lobby import (
        build_lobby_embed,
        MatchLobbyView
    )
    from views.toss_view import build_toss_embed

    match_id = str(match_id)

    matches = load_matches()
    match = matches.get(match_id)

    if match is None:
        logger.error("Countdown stopped: match %s not found", match_id)
        return

    if match.get("status") == "toss":
        logger.info("Match %s has already reached the toss", match_id)
        return

    if match.get("status") == "live":
        logger.info("Match %s is already live", match_id)
        return

    match["status"] = "starting"
    save_matches(matches)

    guild = message.guild

    if guild is None:
        logger.error("Countdown stopped: message has no guild")
        return

    view = MatchLobbyView(match_id)
    for child in view.children:
        child.disabled = True

    try:
        for seconds in (5, 4, 3, 2, 1):
            embed = await build_lobby_embed(guild, match_id)

            # Find the Status field by name instead of relying
            # on a hard-coded embed field index.
            status_index = next(
                (
                    index
                    for index, field in enumerate(embed.fields)
                    if field.name == "Status"
                ),
                None
            )

            if status_index is None:
                embed.add_field(
                    name="Status",
                    value=f"⏳ Match starts in **{seconds}**...",
                    inline=False
                )
            else:
                embed.set_field_at(
                    status_index,
                    name="Status",
                    value=f"⏳ Match starts in **{seconds}**...",
                    inline=False
                )

            await message.edit(embed=embed, view=view)
            logger.info(
                "Match %s countdown: %s",
                match_id,
                seconds
            )

            await asyncio.sleep(1)

        # Verify the match still exists before showing the toss.
        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error("Match %s disappeared before toss", match_id)
            return

        # Build the toss result and update the existing lobby message.
        toss_embed = await build_toss_embed(guild, match_id)

        matches = load_matches()
        match = matches.get(match_id)

        if match is None:
            logger.error("Match %s disappeared while building toss", match_id)
            return

        match["status"] = "toss"
        save_matches(matches)

        await message.edit(embed=toss_embed, view=None)

        logger.info("Match %s toss screen displayed successfully", match_id)

    except discord.NotFound:
        logger.exception(
            "Countdown failed: lobby message %s was not found",
            match_id
        )
        raise

    except discord.Forbidden:
        logger.exception(
            "Countdown failed: bot lacks permission to edit lobby %s",
            match_id
        )
        raise

    except Exception:
        logger.exception(
            "Countdown or toss transition failed for match %s",
            match_id
        )
        raise
