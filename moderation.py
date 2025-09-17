import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import random

MODLOG_CHANNEL_ID = 1352453980294217809
ADMIN_CHANNEL_ID = 1283063768296980501
ADMIN_ROLE_ID = 1261275017195425793

cases = {}  # {case_number: {...}}

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_load(self):
        self.bot.tree.add_command(self.ModerationGroup(self))

    class ModerationGroup(app_commands.Group):
        def __init__(self, cog):
            super().__init__(name="moderation", description="Moderation commands")
            self.cog = cog

        # ========== CORE FUNCTION ==========
        async def handle_case(self, interaction, action, user: discord.Member, reason: str, proof: discord.Attachment = None):
            case_number = random.randint(1000, 9999)
            while case_number in cases:
                case_number = random.randint(1000, 9999)

            cases[case_number] = {
                "action": action,
                "user": user.id,
                "moderator": interaction.user.id,
                "reason": reason,
                "proof": proof.url if proof else None,
                "timestamp": datetime.utcnow().isoformat()
            }

            # Embed for logs
            embed = discord.Embed(
                title=f"{action.upper()} - Case #{case_number}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="👮 Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="🙍 User", value=user.mention, inline=True)
            embed.add_field(name="📖 Reason", value=reason or "Not provided", inline=False)
            if proof:
                embed.set_image(url=proof.url)
            embed.set_footer(text=f"Death Inc | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

            log_channel = interaction.client.get_channel(MODLOG_CHANNEL_ID)
            if log_channel:
                view = discord.ui.View()

                # Button to open appeal
                async def appeal_callback(i: discord.Interaction):
                    if i.user.id != user.id:
                        await i.response.send_message("⚠️ Only the punished user can appeal this case.", ephemeral=True)
                        return

                    # disable button after one use
                    for item in view.children:
                        item.disabled = True
                    await i.message.edit(view=view)

                    # send appeal embed to admins
                    admin_channel = interaction.client.get_channel(ADMIN_CHANNEL_ID)
                    appeal_embed = discord.Embed(
                        title=f"📨 Appeal for Case #{case_number}",
                        description=f"User {user.mention} submitted an appeal.\n\n**Reason Provided:** {reason}",
                        color=discord.Color.orange(),
                        timestamp=datetime.utcnow()
                    )
                    appeal_embed.set_footer(text=f"Death Inc | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

                    appeal_view = discord.ui.View()

                    async def approve_callback(ai: discord.Interaction):
                        if not any(r.id == ADMIN_ROLE_ID for r in ai.user.roles):
                            await ai.response.send_message("❌ Only admins can approve appeals.", ephemeral=True)
                            return
                        await user.send(f"✅ Your appeal for case #{case_number} was **approved**. Thanks for responding.")
                        await ai.response.send_message("✅ Appeal approved and user notified.", ephemeral=True)
                        for item in appeal_view.children:
                            item.disabled = True
                        await ai.message.edit(view=appeal_view)

                    async def reject_callback(ai: discord.Interaction):
                        if not any(r.id == ADMIN_ROLE_ID for r in ai.user.roles):
                            await ai.response.send_message("❌ Only admins can reject appeals.", ephemeral=True)
                            return
                        await user.send(f"❌ Your appeal for case #{case_number} was **rejected**. You were fairly punished.")
                        await ai.response.send_message("❌ Appeal rejected and user notified.", ephemeral=True)
                        for item in appeal_view.children:
                            item.disabled = True
                        await ai.message.edit(view=appeal_view)

                    appeal_view.add_item(discord.ui.Button(label="Approve Appeal", style=discord.ButtonStyle.success, custom_id="approve"))
                    appeal_view.add_item(discord.ui.Button(label="Reject Appeal", style=discord.ButtonStyle.danger, custom_id="reject"))

                    appeal_view.children[0].callback = approve_callback
                    appeal_view.children[1].callback = reject_callback

                    await admin_channel.send(embed=appeal_embed, view=appeal_view)
                    await i.response.send_message("📨 Your appeal has been submitted to admins.", ephemeral=True)

                button = discord.ui.Button(label="Appeal Case", style=discord.ButtonStyle.primary, custom_id=f"appeal_{case_number}")
                button.callback = appeal_callback
                view.add_item(button)
                await log_channel.send(embed=embed, view=view)

            # DM the punished user
            try:
                await user.send(f"⚠️ You have been **{action}** in Death Inc.\nReason: {reason}\nCase #{case_number}\n\nYou may appeal this decision in the server.")
            except:
                pass

            await interaction.response.send_message(f"✅ {user.mention} has been {action}. Case #{case_number} logged.", ephemeral=True)

        # ========== COMMANDS ==========
        @app_commands.command(name="ban", description="Ban a user")
        async def ban(self, interaction, user: discord.Member, reason: str, proof: discord.Attachment = None):
            await self.handle_case(interaction, "Ban", user, reason, proof)
            await user.ban(reason=reason)

        @app_commands.command(name="kick", description="Kick a user")
        async def kick(self, interaction, user: discord.Member, reason: str, proof: discord.Attachment = None):
            await self.handle_case(interaction, "Kick", user, reason, proof)
            await user.kick(reason=reason)

        @app_commands.command(name="warn", description="Warn a user")
        async def warn(self, interaction, user: discord.Member, reason: str, proof: discord.Attachment = None):
            await self.handle_case(interaction, "Warn", user, reason, proof)

        @app_commands.command(name="timeout", description="Timeout a user")
        async def timeout(self, interaction, user: discord.Member, duration: int, reason: str, proof: discord.Attachment = None):
            await self.handle_case(interaction, "Timeout", user, reason, proof)
            until = datetime.utcnow() + timedelta(minutes=duration)
            await user.timeout(until, reason=reason)

        @app_commands.command(name="purge", description="Purge messages")
        async def purge(self, interaction, amount: int):
            if not interaction.channel.permissions_for(interaction.user).manage_messages:
                await interaction.response.send_message("❌ You don’t have permission.", ephemeral=True)
                return
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.response.send_message(f"✅ Deleted {len(deleted)} messages.", ephemeral=True)

        @app_commands.command(name="cases", description="View cases of a user")
        async def cases_cmd(self, interaction, user: discord.Member):
            user_cases = [f"#{cid} - {c['action']} | Reason: {c['reason']}" for cid, c in cases.items() if c['user'] == user.id]
            if not user_cases:
                await interaction.response.send_message(f"ℹ️ No cases found for {user.mention}", ephemeral=True)
                return
            await interaction.response.send_message("\n".join(user_cases), ephemeral=True)

        @app_commands.command(name="deletecase", description="Delete a moderation case")
        async def delete_case(self, interaction, case_number: int):
            if case_number not in cases:
                await interaction.response.send_message("❌ Case not found.", ephemeral=True)
                return
            del cases[case_number]
            await interaction.response.send_message(f"🗑️ Case #{case_number} deleted.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
