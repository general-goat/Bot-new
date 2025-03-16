import discord
from discord.ext import commands
from discord import Embed, app_commands
from datetime import datetime
import json
import os

class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.banned_words = set()
        self.allowed_domains = set()
        self.whitelist_roles = set()
        self.whitelist_channels = set()
        self.logs_channel = None
        self.enabled = True
        self.load_banned_words()

    def load_banned_words(self):
        if os.path.exists("banned_words.json"):
            with open("banned_words.json", "r") as f:
                self.banned_words = set(json.load(f))

    def save_banned_words(self):
        with open("banned_words.json", "w") as f:
            json.dump(list(self.banned_words), f)

    async def log_action(self, action, user, reason, message=None):
        if not self.logs_channel:
            return

        embed = Embed(
            title="🚨 AutoMod Action",
            description=f"**Action:** {action}\n**User:** {user.mention}\n**Reason:** {reason}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        if message:
            embed.add_field(name="Message Content", value=message.content, inline=False)
        embed.set_footer(text="AFW AutoMod", icon_url="https://cdn.discordapp.com/icons/1237101014214250648/a_04e38a5ec6fa6c196647e25653110334.gif?size=1024")

        await self.logs_channel.send(embed=embed)

    async def warn_user(self, user, reason):
        embed = Embed(
            title="⚠️ AutoMod Warning",
            description=f"You have been warned for: **{reason}**",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="AFW AutoMod", icon_url="https://cdn.discordapp.com/icons/1237101014214250648/a_04e38a5ec6fa6c196647e25653110334.gif?size=1024")
        try:
            await user.send(embed=embed)
        except discord.Forbidden:
            pass  # User has DMs disabled

    @app_commands.command(name="automod-setup", description="Set up AutoMod logging channel and enable AutoMod")
    @app_commands.describe(channel="The channel to send logs to")
    async def setup_logs(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.logs_channel = channel
        self.enabled = True
        await interaction.response.send_message(f"✅ AutoMod enabled. Logs channel set to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="automod-disable", description="Disable AutoMod temporarily")
    async def disable_automod(self, interaction: discord.Interaction):
        self.enabled = False
        await interaction.response.send_message("✅ AutoMod disabled.", ephemeral=True)

    @app_commands.command(name="automod-enable", description="Enable AutoMod")
    async def enable_automod(self, interaction: discord.Interaction):
        self.enabled = True
        await interaction.response.send_message("✅ AutoMod enabled.", ephemeral=True)

    @app_commands.command(name="blacklist-words", description="Show the list of blacklisted words")
    async def show_blacklist(self, interaction: discord.Interaction):
        if not self.banned_words:
            await interaction.response.send_message("❌ No words are currently blacklisted.", ephemeral=True)
        else:
            await interaction.response.send_message(f"📜 Blacklisted words: {', '.join(self.banned_words)}", ephemeral=True)

    @app_commands.command(name="automod-ban-word", description="Add a word to the banned words list")
    @app_commands.describe(word="The word to ban")
    async def ban_word(self, interaction: discord.Interaction, word: str):
        self.banned_words.add(word.lower())
        self.save_banned_words()
        await interaction.response.send_message(f"✅ Word '{word}' added to the banned words list.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.enabled or message.author.bot:
            return

        # Check if user or channel is exempt
        if any(role.id in self.whitelist_roles for role in message.author.roles):
            return
        if message.channel.id in self.whitelist_channels:
            return

        # Check for banned words
        for word in self.banned_words:
            if word in message.content.lower():
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, your message was deleted for using a banned word.", delete_after=5)
                await self.log_action("Message Deleted", message.author, "Banned word", message)
                await self.warn_user(message.author, "Using a banned word")
                return

        # Check for links
        if "http" in message.content:
            if not any(domain in message.content for domain in self.allowed_domains):
                await message.delete()
                await message.channel.send(f"⚠️ {message.author.mention}, your message was deleted for containing a link.", delete_after=5)
                await self.log_action("Message Deleted", message.author, "Unauthorized link", message)
                await self.warn_user(message.author, "Posting unauthorized links")
                return

async def setup(bot):
    await bot.add_cog(AutoMod(bot))