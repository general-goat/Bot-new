import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

class GreenTea(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_game = False
        self.registered_players = []
        self.scores = {}
        self.target_score = 0
        self.reward = None
        self.registration_time = 30
        self.current_fragment = None
        self.used_answers = set()  # Track used answers for the current fragment

    # Slash command to start the game
    @app_commands.command(name="greentea-start", description="Start the Green Tea game")
    @app_commands.describe(
        target="The target score to win the game (required)",
        reward="The reward for the winner (optional)",
        registration_time="The time (in seconds) for players to register (default: 30)"
    )
    async def greentea_start(self, interaction: discord.Interaction, target: int, reward: str = None, registration_time: int = 30):
        if self.active_game:
            await interaction.response.send_message("A game is already running!", ephemeral=True)
            return

        self.active_game = True
        self.target_score = target
        self.reward = reward
        self.registration_time = registration_time
        self.registered_players = []
        self.scores = {}
        self.used_answers = set()

        # Send the registration embed
        embed = discord.Embed(title="🍵 Green Tea Game 🍵", color=discord.Color.green())
        embed.add_field(name="Rules", value="""
🔹 **React with 🍵 to join the game!**
🔹 The game will start in **30 seconds**.

📜 **Game Rules:**
1️⃣ A word fragment will be given (e.g., `ing`)
2️⃣ Reply with a real word containing that fragment (e.g., `King`)
3️⃣ First, second, and third correct answers get points!

🏆 **Scoring:**
🥇 First: **5 points**
🥈 Second: **3 points**
🥉 Third: **1 point**

🔸 **First to reach the target wins!**
""", inline=False)
        if reward:
            embed.add_field(name="Reward", value=reward, inline=False)
        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("🍵")

        # Acknowledge the interaction
        await interaction.response.send_message("Green Tea game started! React with 🍵 to join.", ephemeral=True)

        # Wait for registration
        await asyncio.sleep(self.registration_time)

        # Check registered players
        message = await interaction.channel.fetch_message(message.id)
        reaction = discord.utils.get(message.reactions, emoji="🍵")
        if reaction:
            self.registered_players = [user async for user in reaction.users() if not user.bot]

        if not self.registered_players:
            await interaction.followup.send("No one registered for the game. Game canceled.", ephemeral=True)
            self.active_game = False
            return

        # Send registered players embed
        embed = discord.Embed(title="🍵 Registered Players 🍵", color=discord.Color.green())
        embed.description = "\n".join([player.mention for player in self.registered_players])
        await interaction.followup.send(embed=embed)

        # Start the game
        await self.play_game(interaction)

    # Function to play the game
    async def play_game(self, interaction: discord.Interaction):
        while self.active_game:
            # Generate a random word fragment
            self.current_fragment = self.generate_word_fragment()
            self.used_answers = set()  # Reset used answers for the new fragment
            await interaction.channel.send(f"🔍 Word Fragment: `{self.current_fragment}`")

            # Wait for answers
            winners = []
            start_time = asyncio.get_event_loop().time()

            def check(m):
                return (
                    m.author in self.registered_players  # Only registered players can answer
                    and self.current_fragment.lower() in m.content.lower()
                    and m.content.lower() in self.get_real_words()
                    and m.author not in winners
                    and m.content.lower() not in self.used_answers
                )

            while len(winners) < 3:
                try:
                    # Wait for correct answers
                    msg = await self.bot.wait_for("message", check=check, timeout=10 - (asyncio.get_event_loop().time() - start_time))
                    winners.append(msg.author)
                    self.used_answers.add(msg.content.lower())  # Track used answers
                    if len(winners) == 1:
                        await msg.add_reaction("🥇")
                        self.scores[msg.author] = self.scores.get(msg.author, 0) + 5
                    elif len(winners) == 2:
                        await msg.add_reaction("🥈")
                        self.scores[msg.author] = self.scores.get(msg.author, 0) + 3
                    elif len(winners) == 3:
                        await msg.add_reaction("🥉")
                        self.scores[msg.author] = self.scores.get(msg.author, 0) + 1
                except asyncio.TimeoutError:
                    break

            # Update leaderboard
            if winners:
                await self.update_leaderboard(interaction)
            else:
                await interaction.channel.send("No one answered correctly this round.")

            # Check if someone reached the target score
            for player, score in self.scores.items():
                if score >= self.target_score:
                    await interaction.channel.send(f"🎉 {player.mention} has reached the target score of {self.target_score}! Game over.")
                    self.active_game = False
                    await self.final_leaderboard(interaction)
                    return

            # Wait 1 second before the next fragment
            await asyncio.sleep(1)

    # Function to generate a random word fragment
    def generate_word_fragment(self):
        fragments = [
            "ing", "ate", "tion", "ment", "able", "ness", "ify", "est", "less", "ful",
            "ly", "er", "ist", "ism", "ous", "ive", "ize", "age", "al", "ance", "ence",
            "dom", "hood", "ship", "ty", "ity", "ment", "ness", "ship", "th", "ward",
            "wise", "y", "able", "ible", "al", "ant", "ary", "ful", "ic", "ious", "ish",
            "ive", "less", "like", "ous", "some", "worthy", "en", "ify", "ate", "en", "fy"
        ]
        return random.choice(fragments)

    # Function to get real words (dummy implementation)
    def get_real_words(self):
        return [
            "king", "sing", "celebration", "happiness", "beautiful", "establish", "lessen",
            "greatest", "hopeful", "less", "establishment", "establishing", "amazing", "lovely",
            "powerful", "creative", "destruction", "happiness", "friendship", "childhood"
        ]

    # Function to update the leaderboard
    async def update_leaderboard(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏆 Leaderboard 🏆", color=discord.Color.gold())
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        for i, (player, score) in enumerate(sorted_scores):
            embed.add_field(name=f"{i + 1}. {player.name}", value=f"Score: {score}", inline=False)
        await interaction.channel.send(embed=embed)

    # Function to display the final leaderboard
    async def final_leaderboard(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🏆 Final Leaderboard 🏆", color=discord.Color.red())
        sorted_scores = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        for i, (player, score) in enumerate(sorted_scores):
            embed.add_field(name=f"{i + 1}. {player.name}", value=f"Score: {score}", inline=False)
        await interaction.channel.send(embed=embed)

    # Slash command to end the game
    @app_commands.command(name="greentea-end", description="End the Green Tea game")
    async def greentea_end(self, interaction: discord.Interaction):
        if not self.active_game:
            await interaction.response.send_message("No Green Tea game is running at the moment.", ephemeral=True)
            return

        self.active_game = False
        await interaction.response.send_message("The Green Tea game has been ended.", ephemeral=True)
        await self.final_leaderboard(interaction)

# Cog setup function
async def setup(bot):
    await bot.add_cog(GreenTea(bot))