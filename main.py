import discord
from discord.ext import commands
from discord import app_commands
import afk  # Import the AFK cog
import utility  # Import the Utility cog
import greentea  # Import the GreenTea cog
import treasurehunt  # Import the TreasureHunt cog
import sticky  # Import the Sticky cog
import roleusers  # Import the RoleUsers cog
import help  # Import the Help cog
import utility_commands  # Import the new UtilityCommands cog
import automod
import reactionrole
# Initialize the bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents)  # Prefix is irrelevant since we're using slash commands

# Load cogs
async def load_cogs():
    await bot.add_cog(afk.AFK(bot))  # Load AFK cog
    await bot.add_cog(utility.Utility(bot))  # Load Utility cog
    await bot.add_cog(greentea.GreenTea(bot))  # Load GreenTea cog
    await bot.add_cog(treasurehunt.TreasureHunt(bot))  # Load TreasureHunt cog
    await bot.add_cog(sticky.Sticky(bot))  # Load Sticky cog
    await bot.add_cog(roleusers.RoleUsers(bot))  # Load RoleUsers cog
    await bot.add_cog(help.Help(bot))  # Load Help cog
    await bot.add_cog(utility_commands.UtilityCommands(bot))  # Load new UtilityCommands cog
    await bot.add_cog(automod.AutoMod(bot))
    await bot.add_cog(reactiontole.ReactionRoles(bot))
# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await load_cogs()
    try:
        # Sync slash commands
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Error syncing slash commands: {e}")



# Run the bot
bot.run(""
