import discord
from discord.ext import commands
from datetime import datetime

WELCOME_CHANNEL_ID = 1352353471919296522  # put your welcome channel ID here
WELCOME_IMAGE = "https://i.ibb.co/0fj7G2J/black-bg.png"  # black background image

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            return

        # Main Welcome Embed
        embed = discord.Embed(
            title=":deathinc: 𝐖𝐄𝐋𝐂𝐎𝐌𝐄 𝐓𝐎 𝐃𝐄𝐀𝐓𝐇 𝐈𝐍𝐂 🔥",
            description=(
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👋 Welcome {member.mention}!\n"
                "You’ve entered the **Death Inc Alliance**, a Clash network where loyalty meets dominance.\n"
                "We’re more than clans — we’re a family pushing each other to the top. ⚡\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "### 📌 Channels to Check\n\n"
                "➡️ 📢 **Announcements** → [Click Here](https://discord.com/channels/844156696464982017/1394179148175642674)\n"
                "➡️ 📜 **Rules** → [Click Here](https://discord.com/channels/844156696464982017/1394179075509063700)\n"
                "➡️ 🎫 **Tickets** → [Click Here](https://discord.com/channels/844156696464982017/1401433053997437069)\n"
                "➡️ 🏆 **Our Clans** → [Click Here](https://discord.com/channels/844156696464982017/1394192054946365522)\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✨ This is just the beginning — your grind starts now. Welcome to **Death Inc**."
            ),
            color=discord.Color.dark_gray()
        )

        embed.set_image(url=WELCOME_IMAGE)
        embed.set_footer(text=f"Death Inc Welcome | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

        await channel.send(embed=embed)

        # Secondary Avatar Embed
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        count = len(member.guild.members)

        avatar_embed = discord.Embed(
            description=f"👋 Hey {member.mention}, welcome to **Death Inc**!\n\n"
                        f"You're member **#{count}** 🚀",
            color=discord.Color.black()
        )
        avatar_embed.set_image(url=avatar_url)
        avatar_embed.set_footer(text=f"Death Inc Welcome | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

        await channel.send(embed=avatar_embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
