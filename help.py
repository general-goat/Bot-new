import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to display the help embed
    @app_commands.command(name="help", description="List all commands and their descriptions")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🎉 AFW Grand Commands", color=discord.Color.red())

        # AFW Commands
        embed.add_field(
            name="🛌 AFW Commands",
            value="""
            `/afk <reason>` - Set your AFK status.
            `/afklist` - Check who is AFK.
            """,
            inline=False
        )

        # GreenTea Commands
        embed.add_field(
            name="🍵 GreenTea Commands",
            value="""
            `/greentea-start` - Start the Green Tea game.
            `/greentea-submit` - Submit a word for the Green Tea game.
            `/greentea-leaderboard` - Display the Green Tea game leaderboard.
            `/greentea-end` - End the Green Tea game.
            """,
            inline=False
        )

        # TreasureHunt Commands
        embed.add_field(
            name="🔍 TreasureHunt Commands",
            value="""
            `/treasurehunt-setup` - Set up the treasure hunt.
            `/treasurehunt-start` - Start the treasure hunt.
            `/treasurehunt-submit` - Submit a code for the treasure hunt.
            `/treasurehunt-hint` - Provide a hint for a code.
            `/treasurehunt-leaderboard` - Display the treasure hunt leaderboard.
            `/treasurehunt-end` - End the treasure hunt.
            """,
            inline=False
        )

        # Sticky Commands
        embed.add_field(
            name="📌 Sticky Commands",
            value="""
            `/sticky-add <channel> <message>` - Add a sticky message to a channel.
            `/embedsticky-add <channel>` - Add an embed sticky message to a channel.
            `/unstick <message_link>` - Remove a sticky message.
            """,
            inline=False
        )

        # Utility Commands
        embed.add_field(
            name="🛠️ Utility Commands",
            value="""
            `/avatar <user>` - Show the avatar of a user.
            `/userinfo <user>` - Show information about a user.
            `/serverboosts` - Show server boost information.
            `/serverinfo` - Show information about the server.
            `/poll <question>` - Create a poll.
            `/role-users <role>` - Show users with a specific role.
            """,
            inline=False
        )

        # Set server avatar in the embed
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)

        await interaction.response.send_message(embed=embed)

# Cog setup function
async def setup(bot):
    await bot.add_cog(Help(bot))