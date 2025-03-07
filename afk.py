import discord
from discord.ext import commands
import sqlite3

# Database setup for AFK
def initialize_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS afk_users (
            user_id INTEGER PRIMARY KEY,
            reason TEXT
        )
    """)
    conn.commit()
    conn.close()

initialize_db()

class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # AFK Command
    @commands.command(name="afk", description="Set your AFK status")
    async def afk(self, ctx, *, reason="No reason provided"):
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO afk_users (user_id, reason) VALUES (?, ?)", (ctx.author.id, reason))
        conn.commit()
        conn.close()

        # Notify the user they are now AFK
        embed = discord.Embed(title="🛌 AFK", description=f"{ctx.author.mention}, you are now AFK: **{reason}**", color=discord.Color.red())
        await ctx.send(embed=embed)

    # AFK List Command
    @commands.command(name="afklist", description="Check who is AFK")
    async def afklist(self, ctx):
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, reason FROM afk_users")
        afk_users = cursor.fetchall()
        conn.close()

        if afk_users:
            embed = discord.Embed(title="📜 AFK List", color=discord.Color.red())
            for user_id, reason in afk_users:
                user = self.bot.get_user(user_id)
                if user:
                    embed.add_field(name=user.name, value=f"Reason: {reason}", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("No one is AFK right now.")

    # Event: Check for AFK users
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Ignore the AFK command message
        if message.content.startswith("J!afk"):
            return

        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()

        # Check if the user is no longer AFK
        cursor.execute("SELECT reason FROM afk_users WHERE user_id = ?", (message.author.id,))
        result = cursor.fetchone()
        if result:
            # Remove AFK status
            cursor.execute("DELETE FROM afk_users WHERE user_id = ?", (message.author.id,))
            conn.commit()

            # Notify the user they are no longer AFK
            embed = discord.Embed(title="🛌 Welcome Back!", description=f"{message.author.mention}, you are no longer AFK.", color=discord.Color.green())
            await message.channel.send(embed=embed)

        # Check if someone mentioned an AFK user
        for user in message.mentions:
            cursor.execute("SELECT reason FROM afk_users WHERE user_id = ?", (user.id,))
            result = cursor.fetchone()
            if result:
                embed = discord.Embed(title="🛌 AFK", description=f"{user.mention} is AFK: **{result[0]}**", color=discord.Color.red())
                await message.channel.send(embed=embed)

        conn.close()

# Cog setup function
async def setup(bot):
    await bot.add_cog(AFK(bot))