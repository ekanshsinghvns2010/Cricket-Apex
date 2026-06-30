import asyncio

from utils.match_utils import load_matches, save_matches


async def start_countdown(message, match_id):

    matches = load_matches()
    match = matches.get(str(match_id))

    if match is None:
        return

    if match.get("status") == "starting":
        return

    match["status"] = "starting"
    save_matches(matches)

    try:
        embed = message.embeds[0]

        embed.set_field_at(
            len(embed.fields) - 1,
            name="Status",
            value="✅ Both teams full! Match starting in **5** seconds...",
            inline=False
        )

        await message.edit(embed=embed)

        await asyncio.sleep(5)

        embed = message.embeds[0]

        embed.set_field_at(
            len(embed.fields) - 1,
            name="Status",
            value="🪙 Toss Time!",
            inline=False
        )

        await message.edit(embed=embed)

    except Exception:
        pass
