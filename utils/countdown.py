import asyncio
import discord

from utils.match_utils import get_match


async def start_countdown(message, match_id):

    for i in [5, 4, 3, 2, 1]:

        match = get_match(match_id)

        embed = message.embeds[0]

        embed.set_field_at(
            len(embed.fields) - 1,
            name="Status",
            value=f"⏳ Match starts in **{i}**...",
            inline=False
        )

        await message.edit(embed=embed)

        await asyncio.sleep(1)

    embed = message.embeds[0]

    embed.set_field_at(
        len(embed.fields) - 1,
        name="Status",
        value="🪙 Toss Time!",
        inline=False
    )

    await message.edit(embed=embed)