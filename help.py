import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to display the help embed
    @app_commands.command(name="help", description="List all commands and their descriptions")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌟 AFW Grand Commands 🌟",
            description="Here's a list of all available commands and their descriptions.",
            color=discord.Color.blue()
        )

        # AFW Commands
        embed.add_field(
            name="🛌 **AFW Commands**",
            value="""
            `J!afk <reason>` - Set your AFK status.
            `J!afklist` - Check who is AFK.
            """,
            inline=False
        )

        # GreenTea Commands
        embed.add_field(
            name="🍵 **GreenTea Commands**",
            value="""
            `/greentea-start` - Start the Green Tea game.
            `/greentea-leaderboard` - Display the Green Tea game leaderboard.
            `/greentea-end` - End the Green Tea game.
            """,
            inline=True
        )

        # TreasureHunt Commands
        embed.add_field(
            name="🔍 **TreasureHunt Commands**",
            value="""
            `/treasurehunt-setup` - Set up the treasure hunt.
            `/treasurehunt-start` - Start the treasure hunt.
            `/treasurehunt-submit` - Submit a code for the treasure hunt.
            `/treasurehunt-hint` - Provide a hint for a code.
            `/treasurehunt-leaderboard` - Display the treasure hunt leaderboard.
            `/treasurehunt-end` - End the treasure hunt.
            `/treasurehunt-rules` - Shows the rules of treasurehunt
  """,
            inline=False
        )

        # Sticky Commands
        embed.add_field(
            name="📌 **Sticky Commands**",
            value="""
            `/sticky-add` - Add a sticky message to a channel.
            `/unstick` - Remove a sticky message.
            """,
            inline=False
        )

        # Utility Commands
        embed.add_field(
            name="🛠️ **Utility Commands**",
            value="""
            `/avatar` - Show the avatar of a user.
            `/userinfo` - Show information about a user.
            `/serverboosts` - Show server boost information.
            `/serverinfo` - Show information about the server.
            `/poll` - Create a poll.
            `/role-users` - Show users with a specific role.
            """,
            inline=False
        )

        # Set a custom image in the top right corner
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1251109288324104283/1347758268419670097/channel_banner.png?ex=67ccfd33&is=67cbabb3&hm=2b613c0554ec8265cd00df03b00a98d396e99e3190f859e622484881e39b34c6&")  # Replace with your image URL

        # Add a footer
        embed.set_footer(text="Use /help for more information! | AFW Bot")

        await interaction.response.send_message(embed=embed)

# Cog setup function
async def setup(bot):
    await bot.add_cog(Help(bot))
