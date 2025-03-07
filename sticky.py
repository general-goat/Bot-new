import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

# SQLite database configuration
DATABASE_FILE = "sticky.db"

class Sticky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_messages = {}  # Stores sticky messages for each channel
        self.initialize_db()

    # Function to initialize the database
    def initialize_db(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sticky_messages (
                channel_id INTEGER PRIMARY KEY,
                message_id INTEGER,
                content TEXT,
                is_embed INTEGER
            )
        """)
        conn.commit()
        conn.close()

    # Function to save a sticky message to the database
    def save_sticky_message(self, channel_id, message_id, content, is_embed=False):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sticky_messages (channel_id, message_id, content, is_embed)
            VALUES (?, ?, ?, ?)
        """, (channel_id, message_id, content, int(is_embed)))
        conn.commit()
        conn.close()

    # Function to delete a sticky message from the database
    def delete_sticky_message(self, channel_id):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sticky_messages WHERE channel_id = ?", (channel_id,))
        conn.commit()
        conn.close()

    # Function to get a sticky message from the database
    def get_sticky_message(self, channel_id):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT message_id, content, is_embed FROM sticky_messages WHERE channel_id = ?", (channel_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    # Event: When a message is sent in a channel
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if the channel has a sticky message
        sticky_data = self.get_sticky_message(message.channel.id)
        if sticky_data:
            previous_message_id, content, is_embed = sticky_data

            # Delete the previous sticky message
            try:
                previous_message = await message.channel.fetch_message(previous_message_id)
                await previous_message.delete()
            except discord.NotFound:
                pass

            # Resend the sticky message
            if is_embed:
                embed = discord.Embed.from_dict(eval(content))  # Convert string back to embed
                sticky_message = await message.channel.send(embed=embed)
            else:
                sticky_message = await message.channel.send(content)
            self.save_sticky_message(message.channel.id, sticky_message.id, content, is_embed)

    # Slash command to add a sticky message
    @app_commands.command(name="sticky-add", description="Add a sticky message to a channel")
    @app_commands.describe(
        channel="The channel to add the sticky message to",
        message="The message to stick"
    )
    async def sticky_add(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        # Delete the previous sticky message if it exists
        previous_sticky = self.get_sticky_message(channel.id)
        if previous_sticky:
            try:
                previous_message = await channel.fetch_message(previous_sticky[0])
                await previous_message.delete()
            except discord.NotFound:
                pass
            self.delete_sticky_message(channel.id)

        # Send the new sticky message
        sticky_message = await channel.send(message)
        self.save_sticky_message(channel.id, sticky_message.id, message)

        await interaction.response.send_message(f"✅ Sticky message added to {channel.mention}.", ephemeral=True)

    # Slash command to add an embed sticky message
    @app_commands.command(name="embedsticky-add", description="Add an embed sticky message to a channel")
    @app_commands.describe(
        channel="The channel to add the sticky message to"
    )
    async def embedsticky_add(self, interaction: discord.Interaction, channel: discord.TextChannel):
        # Create an embed builder with a dropdown menu
        embed = discord.Embed(title="Embed Sticky Message", description="Use the dropdown to build your embed.", color=discord.Color.blue())
        view = EmbedBuilderView(self.bot, channel)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # Slash command to remove a sticky message
    @app_commands.command(name="unstick", description="Remove a sticky message using its message link")
    @app_commands.describe(
        message_link="The link to the sticky message to remove"
    )
    async def unstick(self, interaction: discord.Interaction, message_link: str):
        try:
            # Extract the message ID from the link
            message_id = int(message_link.split("/")[-1])
            channel_id = int(message_link.split("/")[-2])

            # Fetch the message
            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)

            # Check if the message is a sticky message
            sticky_data = self.get_sticky_message(channel_id)
            if sticky_data and sticky_data[0] == message_id:
                # Delete the sticky message
                await message.delete()
                self.delete_sticky_message(channel_id)
                await interaction.response.send_message("✅ Sticky message removed.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ This is not a sticky message.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to remove sticky message: {e}", ephemeral=True)

# Embed builder view with dropdown menu
class EmbedBuilderView(discord.ui.View):
    def __init__(self, bot, channel):
        super().__init__()
        self.bot = bot
        self.channel = channel
        self.embed = discord.Embed(title="Sticky Embed", description="This is a sticky embed message.", color=discord.Color.red())

    @discord.ui.select(
        placeholder="Choose an embed option",
        options=[
            discord.SelectOption(label="Title", description="Set the embed title"),
            discord.SelectOption(label="Description", description="Set the embed description"),
            discord.SelectOption(label="Color", description="Set the embed color"),
            discord.SelectOption(label="Fields", description="Add fields to the embed"),
            discord.SelectOption(label="Image", description="Set the embed image"),
            discord.SelectOption(label="Thumbnail", description="Set the embed thumbnail"),
            discord.SelectOption(label="Send", description="Send the embed")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "Send":
            # Send the embed
            sticky_message = await self.channel.send(embed=self.embed)
            self.bot.get_cog("Sticky").save_sticky_message(self.channel.id, sticky_message.id, str(self.embed.to_dict()), is_embed=True)
            await interaction.response.send_message("✅ Sticky embed sent.", ephemeral=True)
        else:
            # Show a modal for the selected option
            await interaction.response.send_modal(EmbedBuilderModal(self.bot, self.embed, select.values[0]))

# Embed builder modal with form
class EmbedBuilderModal(discord.ui.Modal):
    def __init__(self, bot, embed, option):
        super().__init__(title=f"Embed Builder - {option}")
        self.bot = bot
        self.embed = embed
        self.option = option

        if option == "Title":
            self.add_item(discord.ui.TextInput(label="Title", placeholder="Enter the embed title", default=self.embed.title or ""))
        elif option == "Description":
            self.add_item(discord.ui.TextInput(label="Description", placeholder="Enter the embed description", default=self.embed.description or "", style=discord.TextStyle.long))
        elif option == "Color":
            self.add_item(discord.ui.TextInput(label="Color (hex)", placeholder="Enter the embed color (e.g., #FF0000)", default=str(self.embed.color) if self.embed.color else ""))
        elif option == "Fields":
            self.add_item(discord.ui.TextInput(label="Fields (key:value)", placeholder="Enter fields as key:value pairs (one per line)", style=discord.TextStyle.long))
        elif option == "Image":
            self.add_item(discord.ui.TextInput(label="Image URL", placeholder="Enter the image URL", default=self.embed.image.url if self.embed.image else ""))
        elif option == "Thumbnail":
            self.add_item(discord.ui.TextInput(label="Thumbnail URL", placeholder="Enter the thumbnail URL", default=self.embed.thumbnail.url if self.embed.thumbnail else ""))

    async def on_submit(self, interaction: discord.Interaction):
        if self.option == "Title":
            self.embed.title = self.children[0].value
        elif self.option == "Description":
            self.embed.description = self.children[0].value
        elif self.option == "Color":
            try:
                self.embed.color = discord.Color.from_str(self.children[0].value)
            except ValueError:
                await interaction.response.send_message("❌ Invalid color format. Use hex (e.g., #FF0000).", ephemeral=True)
                return
        elif self.option == "Fields":
            for line in self.children[0].value.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    self.embed.add_field(name=key.strip(), value=value.strip(), inline=False)
        elif self.option == "Image":
            self.embed.set_image(url=self.children[0].value)
        elif self.option == "Thumbnail":
            self.embed.set_thumbnail(url=self.children[0].value)

        # Show the updated embed preview
        await interaction.response.send_message("Here's your updated embed preview:", embed=self.embed, ephemeral=True)

# Cog setup function
async def setup(bot):
    await bot.add_cog(Sticky(bot))