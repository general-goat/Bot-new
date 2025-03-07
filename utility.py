import discord
from discord.ext import commands
from discord import app_commands, ui
import sqlite3
import asyncio
from datetime import datetime, timedelta

# Database setup for poll votes and AFK
def initialize_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS poll_votes (
            poll_id TEXT,
            user_id INTEGER,
            vote INTEGER,
            PRIMARY KEY (poll_id, user_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS afk_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT
        )
    """)
    conn.commit()
    conn.close()

initialize_db()

# Poll View with Buttons
class PollView(ui.View):
    def __init__(self, poll_id, options, timeout=None):
        super().__init__(timeout=timeout)
        self.poll_id = poll_id
        self.options = options

    @ui.button(label="1️⃣", style=discord.ButtonStyle.primary)
    async def option1(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_vote(interaction, 0)

    @ui.button(label="2️⃣", style=discord.ButtonStyle.primary)
    async def option2(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_vote(interaction, 1)

    @ui.button(label="3️⃣", style=discord.ButtonStyle.primary)
    async def option3(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_vote(interaction, 2)

    @ui.button(label="4️⃣", style=discord.ButtonStyle.primary)
    async def option4(self, interaction: discord.Interaction, button: ui.Button):
        await self.handle_vote(interaction, 3)

    async def handle_vote(self, interaction: discord.Interaction, vote_index: int):
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()

        # Check if user has already voted
        cursor.execute("SELECT vote FROM poll_votes WHERE poll_id = ? AND user_id = ?", (self.poll_id, interaction.user.id))
        result = cursor.fetchone()

        if result:
            await interaction.response.send_message("You have already voted!", ephemeral=True)
        else:
            # Record the vote
            cursor.execute("INSERT INTO poll_votes (poll_id, user_id, vote) VALUES (?, ?, ?)", (self.poll_id, interaction.user.id, vote_index))
            conn.commit()
            await interaction.response.send_message(f"Voted for: **{self.options[vote_index]}**", ephemeral=True)

        conn.close()

# Utility Cog
class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Slash Command: Poll
    @app_commands.command(name="poll", description="Create a poll with a time limit")
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None, time: int = 60):
        options = [option1, option2]
        if option3:
            options.append(option3)
        if option4:
            options.append(option4)

        # Create poll embed
        embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.red())
        for i, option in enumerate(options):
            embed.add_field(name=f"Option {i+1}", value=option, inline=False)
        embed.set_footer(text=f"Poll ends in {time} seconds.")

        # Send poll with buttons
        poll_id = f"{interaction.channel.id}-{interaction.id}"
        view = PollView(poll_id, options, timeout=time)
        await interaction.response.send_message(embed=embed, view=view)

        # Wait for the poll to end
        await asyncio.sleep(time)
        view.stop()

        # Calculate results
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT vote, COUNT(*) FROM poll_votes WHERE poll_id = ? GROUP BY vote", (poll_id,))
        results = cursor.fetchall()
        conn.close()

        # Create results embed
        result_embed = discord.Embed(title="📊 Poll Results", description=question, color=discord.Color.red())
        for i, option in enumerate(options):
            votes = next((count for vote, count in results if vote == i), 0)
            result_embed.add_field(name=f"Option {i+1}", value=f"{option} - {votes} votes", inline=False)
        await interaction.followup.send(embed=result_embed)

    # Slash Command: Avatar
    @app_commands.command(name="avatar", description="Get a user's avatar")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"🖼️ {member.name}'s Avatar", color=discord.Color.red())
        embed.set_image(url=member.avatar.url)
        await interaction.response.send_message(embed=embed)

    # Slash Command: Server Boost Info
    @app_commands.command(name="serverboost", description="Show server boost information")
    async def serverboost(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title="🚀 Server Boost Information", color=discord.Color.red())
        embed.add_field(name="🌟 Boost Level", value=guild.premium_tier, inline=False)
        embed.add_field(name="🔋 Boosts", value=guild.premium_subscription_count, inline=False)
        embed.add_field(name="📈 Next Level Boosts Required", value=f"{max(0, 15 - guild.premium_subscription_count)}", inline=False)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)

    # Slash Command: Server Info
    @app_commands.command(name="serverinfo", description="Show server information")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title="📋 Server Information", color=discord.Color.red())
        embed.add_field(name="🏷️ Name", value=guild.name, inline=False)
        embed.add_field(name="👑 Owner", value=guild.owner, inline=False)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=False)
        embed.add_field(name="📁 Channels", value=len(guild.channels), inline=False)
        embed.add_field(name="🎭 Roles", value=len(guild.roles), inline=False)
        embed.add_field(name="🔋 Boosts", value=guild.premium_subscription_count, inline=False)
        embed.add_field(name="🌟 Boost Level", value=guild.premium_tier, inline=False)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)

    # Slash Command: User Info
    @app_commands.command(name="userinfo", description="Show user information")
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"👤 {member.name}'s Information", color=discord.Color.red())
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="🆔 ID", value=member.id, inline=False)
        embed.add_field(name="🎖️ Top Role", value=member.top_role, inline=False)
        embed.add_field(name="🎭 Roles", value=", ".join([role.mention for role in member.roles]), inline=False)
        embed.add_field(name="🏠 Active Developer", value="Yes" if member.public_flags.active_developer else "No", inline=False)
        await interaction.response.send_message(embed=embed)


        conn.close()

# Cog setup function
async def setup(bot):
    await bot.add_cog(Utility(bot))