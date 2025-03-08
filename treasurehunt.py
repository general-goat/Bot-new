import discord
from discord.ext import commands
from discord import app_commands
import random
import sqlite3

# SQLite database configuration
DATABASE_FILE = "treasurehunt.db"

class TreasureHunt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_hunt = False
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

    # Function to initialize the database
    def initialize_db(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasurehunt (
                channel_id INTEGER PRIMARY KEY,
                message_id INTEGER,
                content TEXT,
                is_embed INTEGER
            )
        """)
        conn.commit()
        conn.close()

    # Function to save a sticky message to the database
    def save_sticky_message(self, channel_id, message_id, content, is_embed=False):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO treasurehunt (channel_id, message_id, content, is_embed)
            VALUES (?, ?, ?, ?)
        """, (channel_id, message_id, content, int(is_embed)))
        conn.commit()
        conn.close()

    # Function to delete a sticky message from the database
    def delete_sticky_message(self, channel_id):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM treasurehunt WHERE channel_id = ?", (channel_id,))
        conn.commit()
        conn.close()

    # Function to get a sticky message from the database
    def get_sticky_message(self, channel_id):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT message_id, content, is_embed FROM treasurehunt WHERE channel_id = ?", (channel_id,))
        result = cursor.fetchone()
        conn.close()
        return result

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

    # Slash command to start the treasure hunt
    @app_commands.command(name="treasurehunt-start", description="Start the treasure hunt")
    @app_commands.describe(
        num_codes="The number of codes to generate (default: 10)",
        channel_ids="Comma-separated list of channel IDs where codes will be hidden"
    )
    async def treasurehunt_start(self, interaction: discord.Interaction, num_codes: int = 10, channel_ids: str = None):
        if self.active_hunt:
            await interaction.response.send_message("A treasure hunt is already running!", ephemeral=True)
            return

        if not self.staff_channel or not self.logs_channel:
            await interaction.response.send_message("❌ Please set up the treasure hunt first using `/treasurehunt-setup`.", ephemeral=True)
            return

        if not channel_ids:
            await interaction.response.send_message("❌ Please provide a list of channel IDs.", ephemeral=True)
            return

        # Parse channel IDs
        channel_ids = [int(id.strip()) for id in channel_ids.split(",")]
        public_channels = []
        for channel_id in channel_ids:
            channel = interaction.guild.get_channel(channel_id)
            if channel and isinstance(channel, discord.TextChannel):
                public_channels.append(channel)

        if not public_channels:
            await interaction.response.send_message("❌ No valid text channels found. Please check the channel IDs.", ephemeral=True)
            return

        # Acknowledge the interaction immediately
        await interaction.response.send_message("Starting the treasure hunt...", ephemeral=True)

        self.active_hunt = True
        self.codes = {}
        self.leaderboard = {}
        self.hints = {}

        # Generate codes and assign them to channels
        for _ in range(num_codes):
            code = self.generate_code()
            location = random.choice(public_channels)
            self.codes[code] = location
            self.hints[code] = f"Hint: Look in {location.mention}."

        # Send the codes to the staff channel for manual hiding
        embed = discord.Embed(title="🔍 Treasure Hunt Codes", color=discord.Color.red())
        for code, location in self.codes.items():
            embed.add_field(name=code, value=f"Location: {location.mention}", inline=False)
        await self.staff_channel.send(embed=embed)

        # Send logs
        embed = discord.Embed(title="🎉 Treasure Hunt Started", color=discord.Color.red())
        embed.add_field(name="Number of Codes", value=num_codes, inline=False)
        await self.logs_channel.send(embed=embed)

    # Slash command to display the rules
    @app_commands.command(name="treasurehunt-rules", description="Display the treasure hunt rules")
    async def treasurehunt_rules(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎉 Treasure Hunt Rules", color=discord.Color.red())
        embed.add_field(name="What is the treasure?", value="The codes hidden within this server.", inline=False)
        embed.add_field(name="How to IDENTIFY the code?", value="The code will be a 9-letter alphanumeric word with 'AFW' in the middle (e.g., ABCAFW123).", inline=False)
        embed.add_field(name="Where to find?", value="The code will be found throughout this server, maybe in channel descriptions, old messages, or other hidden places!", inline=False)
        embed.add_field(name="How to submit?", value="Use `/treasurehunt-submit` to submit your findings.", inline=False)
        embed.add_field(name="Need a hint?", value="Admins can use `/treasurehunt-hint` to provide hints.", inline=False)

        # Send the embed without replying to the command
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Rules sent!", ephemeral=True)

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
                await self.logs_channel.send(embed=embed)
            else:
                await interaction.response.send_message("This code has already been found.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Incorrect code. Keep searching!", ephemeral=True)

    # Slash command to provide a hint
    @app_commands.command(name="treasurehunt-hint", description="Provide a hint for a code")
    @app_commands.describe(
        code="The code to get a hint for"
    )
    async def treasurehunt_hint(self, interaction: discord.Interaction, code: str):
        if not self.active_hunt:
            await interaction.response.send_message("No treasure hunt is running at the moment.", ephemeral=True)
            return

        if code in self.hints:
            await interaction.response.send_message(self.hints[code], ephemeral=True)
        else:
            await interaction.response.send_message("❌ Invalid code. Please check the code and try again.", ephemeral=True)

    # Slash command to display the leaderboard
    @app_commands.command(name="treasurehunt-leaderboard", description="Display the treasure hunt leaderboard")
    async def treasurehunt_leaderboard(self, interaction: discord.Interaction):
        if not self.active_hunt:
            await interaction.response.send_message("No treasure hunt is running at the moment.", ephemeral=True)
            return

        embed = discord.Embed(title="🏆 Treasure Hunt Leaderboard", color=discord.Color.red())
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
        await self.logs_channel.send(embed=embed)

        await interaction.response.send_message("The treasure hunt has ended. All codes are now expired.", ephemeral=True)

# Cog setup functions
async def setup(bot):
    await bot.add_cog(TreasureHunt(bot))
