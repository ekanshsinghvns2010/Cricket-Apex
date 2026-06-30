import asyncio

from utils.match_utils import load_matches, save_matches


async def start_countdown(message, match_id):

    from views.matches_lobby import build_lobby_embed

    print(">>> Countdown function entered")

    matches = load_matches()
    match = matches.get(str(match_id))

    if match is None:
        print("❌ Match not found")
        return

    print("Status before:", repr(match["status"]))
    print(match)

    if match.get("status") == "starting":
        print("❌ Match already starting")
        return

    match["status"] = "starting"
    save_matches(matches)

    print("✅ Status changed to starting")

    guild = message.guild
    from views.matches_lobby import MatchLobbyView
    view = MatchLobbyView(match_id)
    for child in view.children:
        child.disabled = True

    for i in [5, 4, 3, 2, 1]:

        embed = await build_lobby_embed(guild, match_id)

        print("Field count:", len(embed.fields))

        for index, field in enumerate(embed.fields):
            print(index, field.name)

        try:
            embed.set_field_at(
                8,
                name="Status",
                value=f"⏳ Match starts in **{i}**...",
                inline=False
            )

            await message.edit(
                embed=embed,
                view=view
            )

            print(f"✅ Edited countdown {i}")

        except Exception as e:
            print("❌ EDIT ERROR:", e)
            raise

        await asyncio.sleep(1)

    embed = await build_lobby_embed(
        guild,
        match_id
    )

    try:
        embed.set_field_at(
            8,
            name="Status",
            value="🪙 Toss Time!",
            inline=False
        )

        await message.edit(
            embed=embed,
            view=view
        )

        print("✅ Toss screen shown")

    except Exception as e:
        print("❌ FINAL EDIT ERROR:", e)
        raise