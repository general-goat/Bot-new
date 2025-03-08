import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

# SQLite database configuration
DATABASE_FILE = "sticky.db"

class Sticky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_messages = {}  # Stores sticky messages for each channel
        self.initialize_db()

    # Function to initialize the database
    def initialize_db(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sticky_messages (
                channel_id INTEGER PRIMARY KEY,
                message_id INTEGER,
                content TEXT
            )
        """)
        conn.commit()
        conn.close()

    # Function to save a sticky message to the database
    def save_sticky_message(self, channel_id, message_id, content):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sticky_messages (channel_id, message_id, content)
            VALUES (?, ?, ?)
        """, (channel_id, message_id, content))
        conn.commit()
        conn.close()

    # Function to delete a sticky message from the database
    def delete_sticky_message(self, channel_id):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sticky_messages WHERE channel_id = ?", (channel_id,))
        conn.commit()
        conn.close()

    # Function to get a sticky message from the database
    def get_sticky_message(self, channel_id):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT message_id, content FROM sticky_messages WHERE channel_id = ?", (channel_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    # Event: When a message is sent in a channel
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if the channel has a sticky message
        sticky_data = self.get_sticky_message(message.channel.id)
        if sticky_data:
            previous_message_id, content = sticky_data

            # Delete the previous sticky message
            try:
                previous_message = await message.channel.fetch_message(previous_message_id)
                await previous_message.delete()
            except discord.NotFound:
                pass

            # Resend the sticky message
            sticky_message = await message.channel.send(content)
            self.save_sticky_message(message.channel.id, sticky_message.id, content)

    # Slash command to add a sticky message
    @app_commands.command(name="sticky-add", description="Add a sticky message to a channel")
    @app_commands.describe(
        channel="The channel to add the sticky message to",
        message="The message to stick"
    )
    async def sticky_add(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        # Delete the previous sticky message if it exists
        previous_sticky = self.get_sticky_message(channel.id)
        if previous_sticky:
            try:
                previous_message = await channel.fetch_message(previous_sticky[0])
                await previous_message.delete()
            except discord.NotFound:
                pass
            self.delete_sticky_message(channel.id)

        # Send the new sticky message
        sticky_message = await channel.send(message)
        self.save_sticky_message(channel.id, sticky_message.id, message)

        await interaction.response.send_message(f"✅ Sticky message added to {channel.mention}.", ephemeral=True)

    # Slash command to remove a sticky message
    @app_commands.command(name="unstick", description="Remove a sticky message using its message link")
    @app_commands.describe(
        message_link="The link to the sticky message to remove"
    )
    async def unstick(self, interaction: discord.Interaction, message_link: str):
        try:
            # Extract the message ID from the link
            message_id = int(message_link.split("/")[-1])
            channel_id = int(message_link.split("/")[-2])

            # Fetch the message
            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)

            # Check if the message is a sticky message
            sticky_data = self.get_sticky_message(channel_id)
            if sticky_data and sticky_data[0] == message_id:
                # Delete the sticky message
                await message.delete()
                self.delete_sticky_message(channel_id)
                await interaction.response.send_message("✅ Sticky message removed.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ This is not a sticky message.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to remove sticky message: {e}", ephemeral=True)

# Cog setup function
async def setup(bot):
    await bot.add_cog(Sticky(bot))
