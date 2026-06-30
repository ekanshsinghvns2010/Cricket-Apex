import asyncio

from utils.match_utils import load_matches, save_matches


async def start_countdown(message, match_id):

    from views.matches_lobby import build_lobby_embed

    matches = load_matches()
    match = matches.get(str(match_id))

    if match is None:
        return

    if match.get("status") == "starting":
        return

    match["status"] = "starting"
    save_matches(matches)

    guild = message.guild

    for i in [5, 4, 3, 2, 1]:

        embed = await build_lobby_embed(guild, match_id)

        embed.set_field_at(
            8,  # Status field
            name="Status",
            value=f"⏳ Match starts in **{i}**...",
            inline=False
        )

        await message.edit(embed=embed)

        await asyncio.sleep(1)

    embed = await build_lobby_embed(guild, match_id)

    embed.set_field_at(
        8,
        name="Status",
        value="🪙 Toss Time!",
        inline=False
    )

    await message.edit(embed=embed)