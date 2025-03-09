import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from googletrans import Translator
import asyncio
import random

class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect("utility.db")
        self.cursor = self.conn.cursor()
        self.setup_db()
        self.translator = Translator()

    def setup_db(self):
        # Table for reminders
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                user_id INTEGER,
                reminder_text TEXT,
                reminder_time REAL
            )
        """)
        # Table for custom commands
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_commands (
                command_name TEXT PRIMARY KEY,
                command_response TEXT
            )
        """)
        # Table for feedback
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                user_id INTEGER,
                feedback_text TEXT
            )
        """)
        self.conn.commit()

    # Remind command (Slash)
    @app_commands.command(name="remind", description="Set a reminder")
    @app_commands.describe(time="Time in minutes", reminder="What to remind you about")
    async def remind(self, interaction: discord.Interaction, time: float, reminder: str):
        await interaction.response.send_message(f"⏰ **Reminder set!** I'll remind you in **{time} minutes**.")
        await asyncio.sleep(time * 60)
        await interaction.followup.send(f"🔔 **Reminder for {interaction.user.mention}:** {reminder}")

    # Translate command (Slash)
    @app_commands.command(name="translate", description="Translate text to a specified language (default: English)")
    @app_commands.describe(text="Text to translate", language="Target language code (e.g., 'es' for Spanish, default: 'en')")
    async def translate(self, interaction: discord.Interaction, text: str, language: str = "en"):
        try:
            translation = self.translator.translate(text, dest=language)
            embed = discord.Embed(
                title="🌐 Translation",
                description=f"**Original:** {text}\n**Translated ({language}):** {translation.text}",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ **Error translating:** {e}")

    # Coinflip command (Slash)
    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="🪙 Coinflip",
            description=f"The coin landed on **{result}**!",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

    # Custom command creation (Slash)
    @app_commands.command(name="customcommand", description="Create a custom command")
    @app_commands.describe(name="Name of the command", response="Response for the command")
    async def customcommand(self, interaction: discord.Interaction, name: str, response: str):
        try:
            self.cursor.execute("INSERT INTO custom_commands (command_name, command_response) VALUES (?, ?)", (name, response))
            self.conn.commit()
            embed = discord.Embed(
                title="✅ Custom Command Created",
                description=f"Command `{name}` has been created with the response: `{response}`",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        except sqlite3.IntegrityError:
            await interaction.response.send_message(f"❌ **Error:** Command `{name}` already exists!", ephemeral=True)

    # Delete custom command (Slash)
    @app_commands.command(name="deletecommand", description="Delete a custom command")
    @app_commands.describe(name="Name of the command to delete")
    async def deletecommand(self, interaction: discord.Interaction, name: str):
        self.cursor.execute("DELETE FROM custom_commands WHERE command_name = ?", (name,))
        self.conn.commit()
        if self.cursor.rowcount > 0:
            embed = discord.Embed(
                title="✅ Custom Command Deleted",
                description=f"Command `{name}` has been deleted.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ **Error:** Command `{name}` not found!", ephemeral=True)

    # List custom commands (Slash)
    @app_commands.command(name="listcommands", description="List all custom commands")
    async def listcommands(self, interaction: discord.Interaction):
        self.cursor.execute("SELECT command_name FROM custom_commands")
        commands = self.cursor.fetchall()
        if commands:
            command_list = "\n".join(f"- `{cmd[0]}`" for cmd in commands)
            embed = discord.Embed(
                title="📜 Custom Commands",
                description=command_list,
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ **No custom commands found!**", ephemeral=True)

    # Feedback command (Slash)
    @app_commands.command(name="feedback", description="Send feedback to the bot owner")
    @app_commands.describe(feedback="Your feedback")
    async def feedback(self, interaction: discord.Interaction, feedback: str):
        self.cursor.execute("INSERT INTO feedback (user_id, feedback_text) VALUES (?, ?)", (interaction.user.id, feedback))
        self.conn.commit()
        embed = discord.Embed(
            title="✅ Feedback Sent",
            description="Thank you for your feedback! It has been recorded.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    # Feedback list command (Slash)
    @app_commands.command(name="feedbacklist", description="List all feedbacks (Staff only)")
    async def feedbacklist(self, interaction: discord.Interaction):
        self.cursor.execute("SELECT user_id, feedback_text FROM feedback")
        feedbacks = self.cursor.fetchall()
        if feedbacks:
            feedback_list = "\n".join(f"- <@{fb[0]}>: {fb[1]}" for fb in feedbacks)
            embed = discord.Embed(
                title="📜 Feedback List",
                description=feedback_list,
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ **No feedbacks found!**", ephemeral=True)

    # Message listener for custom commands (Prefix)
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # Check if the message starts with the prefix
        if message.content.startswith("J!"):
            command_name = message.content[2:].lower()  # Remove the "J!" and convert to lowercase
            self.cursor.execute("SELECT command_response FROM custom_commands WHERE command_name = ?", (command_name,))
            result = self.cursor.fetchone()

            if result:
                response = result[0]
                await message.channel.send(response)

# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(UtilityCommands(bot))