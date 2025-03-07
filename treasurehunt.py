import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import sqlite3
from datetime import datetime

# SQLite database configuration
DATABASE_FILE = "treasurehunt.db"

class TreasureHunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_hunt = False
        self.current_event_code = None  # Unique event code for the current hunt
        self.codes = {}  # Stores codes and their locations
        self.leaderboard = {}  # Tracks players' progress
        self.hints = {}  # Stores hints for each code
        self.staff_channel = None  # Channel to send code locations
        self.logs_channel = None  # Channel to send logs

    # Function to generate a random alphanumeric code with "AFW" in the middle
    def generate_code(self):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        prefix = "".join(random.choices(letters, k=3))
        suffix = "".join(random.choices(letters, k=3))
        return f"{prefix}AFW{suffix}"

    # Function to generate a unique event code
    def generate_event_code(self):
        return f"TH{random.randint(100, 999)}"

    # Function to initialize the database
    def initialize_db(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasurehunt (
                event_code TEXT,
                code TEXT,
                location TEXT,
                found_by TEXT
            )
        """)
        conn.commit()
        conn.close()

    # Slash command to set up the treasure hunt
    @app_commands.command(name="treasurehunt-setup", description="Set up the treasure hunt")
    @app_commands.describe(
        staff_channel="The channel to send code locations (e.g., #staff-chat)",
        logs_channel="The channel to send logs (e.g., #logs)"
    )
    async def treasurehunt_setup(self, interaction: discord.Interaction, staff_channel: discord.TextChannel, logs_channel: discord.TextChannel):
        self.staff_channel = staff_channel
        self.logs_channel = logs_channel
        await interaction.response.send_message(f"✅ Treasure hunt setup complete!\nStaff Channel: {staff_channel.mention}\nLogs Channel: {logs_channel.mention}", ephemeral=True)

    # Slash command to send the treasure hunt rules embed
    @app_commands.command(name="treasurehunt-embed", description="Send the treasure hunt rules embed")
    async def treasurehunt_embed(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎉 Treasure Hunt Rules", color=discord.Color.red())
        embed.add_field(name="What is the treasure?", value="The codes hidden within this server.", inline=False)
        embed.add_field(name="How to IDENTIFY the code?", value="The code will be a 9-letter alphanumeric word with 'AFW' in the middle (e.g., ABCAFW123).", inline=False)
        embed.add_field(name="Where to find?", value="The code will be found throughout this server, maybe in channel topics, pinned messages, or embeds!", inline=False)
        embed.add_field(name="How to submit?", value="Use `/treasurehunt-submit` to submit your findings.", inline=False)
        embed.add_field(name="Need a hint?", value="Admins can use `/treasurehunt-hint` to provide hints.", inline=False)
        await interaction.response.send_message(embed=embed)

    # Slash command to start the treasure hunt
    @app_commands.command(name="treasurehunt-start", description="Start the treasure hunt")
    @app_commands.describe(
        num_codes="The number of codes to generate (default: 10)"
    )
    async def treasurehunt_start(self, interaction: discord.Interaction, num_codes: int = 10):
        if self.active_hunt:
            await interaction.response.send_message("A treasure hunt is already running!", ephemeral=True)
            return

        if not self.staff_channel or not self.logs_channel:
            await interaction.response.send_message("❌ Please set up the treasure hunt first using `/treasurehunt-setup`.", ephemeral=True)
            return

        self.active_hunt = True
        self.current_event_code = self.generate_event_code()
        self.codes = {}
        self.leaderboard = {}
        self.hints = {}

        # Generate codes and hide them in random public channels
        public_channels = [channel for channel in interaction.guild.text_channels if not channel.is_private]
        for _ in range(num_codes):
            code = self.generate_code()
            location = random.choice(public_channels)
            self.codes[code] = location
            self.hints[code] = f"Hint: Look in {location.mention}."

            # Hide the code in the channel (e.g., in the topic or a pinned message)
            await location.edit(topic=f"Treasure Hunt Code: {code}")

        # Send the codes to the staff channel
        embed = discord.Embed(title="🔍 Treasure Hunt Codes", color=discord.Color.red())
        for code, location in self.codes.items():
            embed.add_field(name=code, value=location.mention, inline=False)
        await self.staff_channel.send(embed=embed)

        # Send logs
        embed = discord.Embed(title="🎉 Treasure Hunt Started", color=discord.Color.red())
        embed.add_field(name="Event Code", value=self.current_event_code, inline=False)
        embed.add_field(name="Number of Codes", value=num_codes, inline=False)
        await self.logs_channel.send(embed=embed)

        # Send the rules embed
        await self.treasurehunt_embed(interaction)

    # Slash command to submit a code
    @app_commands.command(name="treasurehunt-submit", description="Submit a code for the treasure hunt")
    async def treasurehunt_submit(self, interaction: discord.Interaction, code: str):
        if not self.active_hunt:
            await interaction.response.send_message("No treasure hunt is running at the moment.", ephemeral=True)
            return

        if code in self.codes:
            if code not in self.leaderboard.values():
                self.leaderboard[interaction.user.id] = code
                await interaction.response.send_message(f"🎉 Correct! You found the code: `{code}`.", ephemeral=True)

                # Send logs to the logs channel
                embed = discord.Embed(title="🔍 Code Found", color=discord.Color.red())
                embed.add_field(name="Player", value=interaction.user.mention, inline=False)
                embed.add_field(name="Code", value=code, inline=False)
                embed.add_field(name="Event Code", value=self.current_event_code, inline=False)
                await self.logs_channel.send(embed=embed)
            else:
                await interaction.response.send_message("This code has already been found.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Incorrect code. Keep searching!", ephemeral=True)

    # Slash command to provide a hint
    @app_commands.command(name="treasurehunt-hint", description="Provide a hint for a code")
    async def treasurehunt_hint(self, interaction: discord.Interaction):
        if not self.active_hunt:
            await interaction.response.send_message("No treasure hunt is running at the moment.", ephemeral=True)
            return

        hint = random.choice(list(self.hints.values()))
        await interaction.response.send_message(hint, ephemeral=True)

    # Slash command to display the leaderboard
    @app_commands.command(name="treasurehunt-leaderboard", description="Display the treasure hunt leaderboard")
    async def treasurehunt_leaderboard(self, interaction: discord.Interaction, event_code: str = None):
        if not self.active_hunt and not event_code:
            await interaction.response.send_message("No treasure hunt is running at the moment.", ephemeral=True)
            return

        embed = discord.Embed(title="🏆 Treasure Hunt Leaderboard", color=discord.Color.red())
        if event_code:
            embed.add_field(name="Event Code", value=event_code, inline=False)
        for user_id, code in self.leaderboard.items():
            user = await self.bot.fetch_user(user_id)
            embed.add_field(name=user.name, value=f"Found: `{code}`", inline=False)
        await interaction.response.send_message(embed=embed)

    # Slash command to end the treasure hunt
    @app_commands.command(name="treasurehunt-end", description="End the treasure hunt")
    async def treasurehunt_end(self, interaction: discord.Interaction):
        if not self.active_hunt:
            await interaction.response.send_message("No treasure hunt is running at the moment.", ephemeral=True)
            return

        self.active_hunt = False
        self.codes = {}
        self.leaderboard = {}
        self.hints = {}

        # Send logs
        embed = discord.Embed(title="🔚 Treasure Hunt Ended", color=discord.Color.red())
        embed.add_field(name="Event Code", value=self.current_event_code, inline=False)
        await self.logs_channel.send(embed=embed)

        await interaction.response.send_message("The treasure hunt has ended. All codes are now expired.", ephemeral=True)

# Cog setup function
async def setup(bot):
    await bot.add_cog(TreasureHunt(bot))