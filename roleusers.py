import discord
from discord.ext import commands
from discord import app_commands

class RoleUsers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash command to show users with a specific role
    @app_commands.command(name="role-users", description="Show users with a specific role")
    @app_commands.describe(
        role="The role to check"
    )
    async def role_users(self, interaction: discord.Interaction, role: discord.Role):
        members = [member.mention for member in role.members]
        if members:
            embed = discord.Embed(title=f"👥 Users with {role.name}", color=discord.Color.red())
            embed.description = "\n".join(members)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"No users have the role {role.name}.", ephemeral=True)

# Cog setup function
async def setup(bot):
    await bot.add_cog(RoleUsers(bot))