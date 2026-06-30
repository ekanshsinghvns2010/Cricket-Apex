import random
from discord.ext import commands

from utils.match_utils import (
    load_matches,
    save_matches,
    find_player_match
)

from views.matches_lobby import (
    build_lobby_embed,
    MatchLobbyView
)
from utils.countdown import start_countdown

DEVELOPER_ID = 1451236422785958040


def setup_dev(bot):

    @bot.command(name="fill")
    async def fill(ctx):

        if ctx.author.id != DEVELOPER_ID:
            await ctx.send("❌ This command is only available to the developer.")
            return

        match_id = find_player_match(ctx.author.id)

        if match_id is None:
            await ctx.send("❌ You are not in any match.")
            return

        matches = load_matches()
        match = matches[match_id]

        bot_names = [
            "Aarav", "Vivaan", "Kabir", "Rohan",
            "Aryan", "Viraj", "Aditya", "Dev",
            "Krish", "Yash", "Ishaan", "Ayaan"
        ]

        bot_roles = [
            "Aggressive Batter",
            "Anchor Batter",
            "Finisher",
            "Fast Bowler",
            "Fast Swing Bowler",
            "Spinner",
            "All-Rounder"
        ]

        # Fill Red Team
        while len(match["red_team"]) + len(match["red_bots"]) < match["team_size"]:
            match["red_bots"].append({
                "name": random.choice(bot_names),
                "role": random.choice(bot_roles)
            })

        # Fill Blue Team
        while len(match["blue_team"]) + len(match["blue_bots"]) < match["team_size"]:
            match["blue_bots"].append({
                "name": random.choice(bot_names),
                "role": random.choice(bot_roles)
            })

        save_matches(matches)

        try:
            channel = bot.get_channel(int(match["channel_id"]))

            if channel is None:
                await ctx.send("❌ Couldn't find the match channel.")
                return
            print("Match ID:",match_id)
            print("Channel ID:",match["channel_id"])
            print("Message ID:",match["message_id"])
            message = await channel.fetch_message(
                int(match["message_id"])
            )

            embed = await build_lobby_embed(
                ctx.guild,
                match_id
            )

            await message.edit(
                embed=embed,
                view=MatchLobbyView(match_id)
            )
            print("✅ Lobby message edited successfully")
            from utils.countdown import start_countdown
            print ("Red Humans:",len(match["red_team"]))
            print ("Red Bots:",len(match["red_bots"]))
            print ("Blue Humans:",len(match["blue_team"]))
            print ("Blue Bots:",len(match["blue_bots"]))
            print ("Team Size :",match["team_size"])

            red_full = (len(match["red_team"]) + len(match["red_bots"])
                       )
            blue_full =(len(match["blue_team"]) + len(match["blue_bots"])
                       )
            print(f"Red total = {red_full}")
            print(f"Blue total = {blue_full}")
            print(f"Required = {match['team_size']}")
            #Temporary force the countdown
            print(">>> Calling countdown...")
            await start_countdown(message, match_id)
            print("Status before countdown call:", match["status"])
            print(">>> Countdown finished")
            
            

            await ctx.send("✅ Lobby filled and refreshed!")

        except Exception as e:
            await ctx.send(f"❌ Fill Error: {type(e).__name__}: {e}")
            raise