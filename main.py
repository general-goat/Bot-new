import discord
from discord.ext import commands, tasks
from discord import app_commands
import os

# Import all your cogs
import afk
import utility
import greentea
import treasurehunt
import sticky
import roleusers
import help
import utility_commands
import automod
import reactionrole
import Welcome
import moderation

# ---------------------------
# Intents and bot setup
# ---------------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Required for message content

bot = commands.Bot(command_prefix="!", intents=intents)  # Prefix is irrelevant since we're using slash commands

# ---------------------------
# Status setup
# ---------------------------
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')
    
    # Set status
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name="General the Goat")
    )
    
    # Load all cogs
    await load_cogs()
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Error syncing slash commands: {e}")

# ---------------------------
# Load all cogs
# ---------------------------
async def load_cogs():
    await bot.add_cog(afk.AFK(bot))
    await bot.add_cog(utility.Utility(bot))
    await bot.add_cog(greentea.GreenTea(bot))
    await bot.add_cog(treasurehunt.TreasureHunt(bot))
    await bot.add_cog(sticky.Sticky(bot))
    await bot.add_cog(roleusers.RoleUsers(bot))
    await bot.add_cog(help.Help(bot))
    await bot.add_cog(utility_commands.UtilityCommands(bot))
    await bot.add_cog(automod.AutoMod(bot))
    await bot.add_cog(reactionrole.ReactionRoles(bot))
    await bot.add_cog(Welcome.Welcome(bot))
    await bot.add_cog(moderation.Moderation(bot))
    print("✅ All cogs loaded successfully!")

# ---------------------------
# Run the bot
# ---------------------------
TOKEN = os.getenv("DISCORD_TOKEN")  # Use env variable for safety
if not TOKEN:
    print("❌ ERROR: Discord token not found in environment variables!")
else:
    bot.run(TOKEN)
