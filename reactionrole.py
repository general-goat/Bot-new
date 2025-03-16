import discord
from discord.ext import commands
from discord import app_commands

class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_panels = {}  # Stores role panels: {message_id: {emoji: role_id}}
        self.enabled = True

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not self.enabled or payload.message_id not in self.role_panels:
            return

        guild = self.bot.get_guild(payload.guild_id)
        role_id = self.role_panels[payload.message_id].get(str(payload.emoji))
        if role_id:
            role = guild.get_role(role_id)
            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not self.enabled or payload.message_id not in self.role_panels:
            return

        guild = self.bot.get_guild(payload.guild_id)
        role_id = self.role_panels[payload.message_id].get(str(payload.emoji))
        if role_id:
            role = guild.get_role(role_id)
            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    await member.remove_roles(role)

    @app_commands.command(name="create-role-panel", description="Create a reaction role panel")
    @app_commands.describe(message_id="The message ID to add reactions to", emoji="The emoji to use", role="The role to assign")
    async def create_role_panel(self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):
        try:
            message_id = int(message_id)
            message = await interaction.channel.fetch_message(message_id)
            await message.add_reaction(emoji)
            if message_id not in self.role_panels:
                self.role_panels[message_id] = {}
            self.role_panels[message_id][emoji] = role.id
            await interaction.response.send_message(f"✅ Role panel created: {emoji} → {role.name}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to create role panel: {e}", ephemeral=True)

    @app_commands.command(name="disable-reaction-roles", description="Disable reaction roles temporarily")
    async def disable_reaction_roles(self, interaction: discord.Interaction):
        self.enabled = False
        await interaction.response.send_message("✅ Reaction roles disabled.", ephemeral=True)

    @app_commands.command(name="enable-reaction-roles", description="Enable reaction roles")
    async def enable_reaction_roles(self, interaction: discord.Interaction):
        self.enabled = True
        await interaction.response.send_message("✅ Reaction roles enabled.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))