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
            `/greentea-single` - In development, please don't try.
            """,
            inline=False
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
            `/treasurehunt-rules` - Show the rules of the treasure hunt.
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
            `/remind <time> <reminder>` - Set a reminder.
            `/translate <text> <language>` - Translate text to a specified language.
            `/coinflip` - Flip a coin.
            `/customcommand <name> <response>` - Create a custom command (Staff only).
            `/deletecommand <name>` - Delete a custom command (Staff only).
            `/listcommands` - List all custom commands (Staff only).
            `/feedback <feedback>` - Send feedback to the bot owner.
            """,
            inline=False
        )

        # Set a custom image in the top right corner
        embed.set_thumbnail(url="https://cdn.discordapp.com/icons/1237101014214250648/a_04e38a5ec6fa6c196647e25653110334.gif?size=1024")  # Replace with your image URL

        # Add a footer with AFW branding
        embed.set_footer(
            text="AFW Bot | Empowering Your Server Since 2025",
            icon_url="https://cdn.discordapp.com/icons/1237101014214250648/a_04e38a5ec6fa6c196647e25653110334.gif?size=1024"  # Replace with your server icon URL
        )

        # Add the banner at the bottom
        embed.set_image(url="https://cdn.discordapp.com/attachments/1251109288324104283/1348105351882346577/channel_banner.png")

        await interaction.response.send_message(embed=embed)

# Cog setup function
async def setup(bot):
    await bot.add_cog(Help(bot))
