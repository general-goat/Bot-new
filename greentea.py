import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import asyncio
import random

class GreenTea(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.green_tea_active = False
        self.green_tea_players = []
        self.green_tea_target_points = 10
        self.used_words = set()
        self.used_fragments = set()
        self.common_fragments = [
            "ing", "ed", "er", "est", "ly", "tion", "ment", "ness", "able", "ible",
            "ful", "less", "ous", "al", "ive", "ic", "ish", "ant", "ent", "ism",
            "ist", "ize", "ise", "age", "ance", "ence", "dom", "hood", "ship", "ty",
            "ify", "ate", "en", "ify", "ify", "ify", "ify", "ify", "ify", "ify",
            "acy", "ance", "ence", "ancy", "ency", "dom", "hood", "ism", "ist", "ity",
            "ment", "ness", "ship", "sion", "tion", "ate", "en", "ify", "fy", "ize",
            "ise", "able", "ible", "al", "ial", "ant", "ent", "ary", "ery", "ory",
            "ful", "ic", "ical", "ish", "ive", "less", "ly", "ous", "eous", "ious",
            "y", "al", "an", "ar", "ary", "ed", "en", "er", "est", "ful", "ic", "ing",
            "ish", "ive", "less", "ly", "ment", "ness", "ous", "s", "y", "age", "ance",
            "ence", "ancy", "ency", "dom", "hood", "ism", "ist", "ity", "ment", "ness",
            "ship", "sion", "tion", "ate", "en", "ify", "fy", "ize", "ise", "able",
            "ible", "al", "ial", "ant", "ent", "ary", "ery", "ory", "ful", "ic", "ical",
            "ish", "ive", "less", "ly", "ous", "eous", "ious", "y", "al", "an", "ar",
            "ary", "ed", "en", "er", "est", "ful", "ic", "ing", "ish", "ive", "less",
            "ly", "ment", "ness", "ous", "s", "y", "age", "ance", "ence", "ancy", "ency",
            "dom", "hood", "ism", "ist", "ity", "ment", "ness", "ship", "sion", "tion",
            "ate", "en", "ify", "fy", "ize", "ise", "able", "ible", "al", "ial", "ant",
            "ent", "ary", "ery", "ory", "ful", "ic", "ical", "ish", "ive", "less", "ly",
            "ous", "eous", "ious", "y", "al", "an", "ar", "ary", "ed", "en", "er", "est",
            "ful", "ic", "ing", "ish", "ive", "less", "ly", "ment", "ness", "ous", "s", "y"
        ]
        self.conn = sqlite3.connect("greentea.db")
        self.cursor = self.conn.cursor()
        self.setup_db()

    def setup_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS greentea_scores (
                user_id INTEGER PRIMARY KEY,
                wins INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()

    @app_commands.command(name="greentea_start", description="Start a Green Tea game!")
    @app_commands.describe(point_goal="Points needed to win (Default: 10)", reg_time="Registration time in seconds (Default: 30)")
    async def greentea_start(self, interaction: discord.Interaction, point_goal: int = 10, reg_time: int = 30):
        if self.green_tea_active:
            await interaction.response.send_message("❌ A Green Tea game is already running!", ephemeral=True)
            return

        self.green_tea_active = True
        self.green_tea_players = []
        self.green_tea_target_points = point_goal

        embed = discord.Embed(
            title="🍵 Green Tea Game Registration",
            description=f"🔹 **React with 🍵 to join the game!**\n🔹 The game will start in **{reg_time} seconds**.\n\n"
                        "📜 **Game Rules:**\n"
                        "1️⃣ A word fragment will be given (e.g., `ing`)\n"
                        "2️⃣ Reply with a real word containing that fragment (e.g., `King`)\n"
                        "3️⃣ First, second, and third correct answers get points!\n\n"
                        "🏆 **Scoring:**\n"
                        "🥇 First: **5 points**\n"
                        "🥈 Second: **3 points**\n"
                        "🥉 Third: **1 point**\n\n"
                        "🔸 **First to reach {point_goal} points wins!**",
            color=discord.Color.green()
        )
        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("🍵")

        await asyncio.sleep(reg_time)
        message = await interaction.channel.fetch_message(message.id)

        for reaction in message.reactions:
            if str(reaction.emoji) == "🍵":
                async for user in reaction.users():
                    if user != self.bot.user:
                        self.green_tea_players.append(user)

        if not self.green_tea_players:
            await interaction.channel.send("⚠️ No players joined. Game cancelled.")
            self.green_tea_active = False
            return

        await interaction.channel.send(f"✅ **{len(self.green_tea_players)} players joined:**\n" + "\n".join(f"- {p.mention}" for p in self.green_tea_players))
        asyncio.create_task(self.green_tea_game(interaction.channel))

    async def green_tea_game(self, channel):
        scores = {player: 0 for player in self.green_tea_players}

        while self.green_tea_active and max(scores.values(), default=0) < self.green_tea_target_points:
            available_fragments = [w for w in self.common_fragments if w not in self.used_fragments]
            if not available_fragments:
                await channel.send("🔄 No more unique word fragments available. Game over.")
                break

            word_fragment = random.choice(available_fragments)
            self.used_fragments.add(word_fragment)
            await channel.send(f"🔤 **Next Fragment:** `{word_fragment}`\n(Reply with a word containing this!)")

            def check(m):
                return (m.author in self.green_tea_players 
                        and word_fragment.lower() in m.content.lower() 
                        and m.content.lower() not in self.used_words)

            responses = []
            try:
                while True:
                    msg = await self.bot.wait_for("message", timeout=10, check=check)
                    if msg.author not in [r[0] for r in responses]:  
                        responses.append((msg.author, msg.content, msg))
                        self.used_words.add(msg.content.lower())
                        await msg.add_reaction(["🥇", "🥈", "🥉"][len(responses)-1])
            except asyncio.TimeoutError:
                pass

            for i, (author, _, _) in enumerate(responses[:3]):
                scores[author] += [5, 3, 1][i]

            embed = discord.Embed(title="🏆 Round Results!", color=discord.Color.gold())
            leaderboard = "\n".join(f"**{i+1}. {player.name}** - {points} pts" for i, (player, points) in enumerate(sorted(scores.items(), key=lambda x: x[1], reverse=True)))
            embed.add_field(name="📊 Current Standings:", value=leaderboard, inline=False)

            await channel.send(embed=embed)

        winner = max(scores, key=scores.get)
        await channel.send(f"🎉 **{winner.mention} wins the Green Tea game!**")
        self.green_tea_active = False
        self.used_fragments.clear()
        self.used_words.clear()

    @app_commands.command(name="greentea_end", description="Stop an ongoing Green Tea game")
    async def greentea_end(self, interaction: discord.Interaction):
        if not self.green_tea_active:
            await interaction.response.send_message("❌ No active Green Tea game to stop!", ephemeral=True)
            return
        self.green_tea_active = False
        await interaction.response.send_message("🛑 Green Tea game has been stopped.")

    @app_commands.command(name="greentea_leaderboard", description="Show the leaderboard for the current game or lifetime stats")
    async def greentea_leaderboard(self, interaction: discord.Interaction):
        if not self.green_tea_active:
            await interaction.response.send_message("❌ No active Green Tea game. Use `/greentea_start` to start one!", ephemeral=True)
            return

        scores = {player: 0 for player in self.green_tea_players}
        embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())
        leaderboard = "\n".join(f"**{i+1}. {player.name}** - {points} pts" for i, (player, points) in enumerate(sorted(scores.items(), key=lambda x: x[1], reverse=True)))
        embed.add_field(name="📊 Current Standings:", value=leaderboard, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="greentea_single", description="Start an individual Green Tea game")
    async def greentea_single(self, interaction: discord.Interaction):
        if self.green_tea_active:
            await interaction.response.send_message("❌ A Green Tea game is already running!", ephemeral=True)
            return

        self.green_tea_active = True
        self.green_tea_players = [interaction.user]
        self.green_tea_target_points = 10

        await interaction.response.send_message("🎮 Starting an individual Green Tea game...")
        asyncio.create_task(self.green_tea_single_game(interaction.channel))

    async def green_tea_single_game(self, channel):
        lives = {player: 2 for player in self.green_tea_players}

        while self.green_tea_active and len(lives) > 1:
            available_fragments = [w for w in self.common_fragments if w not in self.used_fragments]
            if not available_fragments:
                await channel.send("🔄 No more unique word fragments available. Game over.")
                break

            word_fragment = random.choice(available_fragments)
            self.used_fragments.add(word_fragment)
            await channel.send(f"🔤 **Next Fragment:** `{word_fragment}`\n(Reply with a word containing this!)")

            def check(m):
                return (m.author in lives 
                        and word_fragment.lower() in m.content.lower() 
                        and m.content.lower() not in self.used_words)

            try:
                msg = await self.bot.wait_for("message", timeout=10, check=check)
                self.used_words.add(msg.content.lower())
                await msg.add_reaction("✅")
            except asyncio.TimeoutError:
                for player in lives:
                    lives[player] -= 1
                    if lives[player] == 0:
                        del lives[player]
                        await channel.send(f"❌ {player.mention} is out of lives!")

        winner = list(lives.keys())[0]
        await channel.send(f"🎉 **{winner.mention} wins the individual Green Tea game!**")
        self.green_tea_active = False
        self.used_fragments.clear()
        self.used_words.clear()

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(GreenTea(bot))
