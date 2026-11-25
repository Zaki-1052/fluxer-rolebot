import fluxer
from fluxer import Cog
from urllib.parse import urlparse

from util.admin import is_admin
from util.database import (
    delete_configured_message_id,
    get_configured_message,
    set_configured_message,
)
import logging

logger = logging.getLogger(__name__)


class Admin(Cog):
    def __init__(self, bot: fluxer.Bot):
        super().__init__(bot)

    @Cog.command()
    async def setmessage(self, ctx: fluxer.Message):
        """
        Configure the message that users will react to for role assignment. The command expects a link to the message in the format: `!role setmessage <message_link>`.
        The channel and message ID are extracted from the link and stored in the database for later reference when handling reactions.
        """
        if ctx.guild_id is None:
            await ctx.reply("This command can only be used in a server.")
            return

        if not await is_admin(self.bot, ctx):
            await ctx.reply("You need administrator permissions to use this command.")
            return

        parsed_link = urlparse(ctx.content.split()[-1])
        if not parsed_link.path:
            await ctx.reply("Invalid message link format.")
            return

        split_path = parsed_link.path.split("/")
        if len(split_path) < 5 or split_path[-4] != "channels":
            await ctx.reply("Invalid message link format.")
            return

        try:
            guild_id = int(split_path[-3])
            channel_id = int(split_path[-2])
            msg_id = int(split_path[-1])
        except ValueError:
            await ctx.reply("Invalid message link format.")
            return

        if guild_id != ctx.guild_id:
            await ctx.reply("The linked message must be in the same server.")
            return

        set_configured_message(ctx.guild_id, channel_id, msg_id)
        await ctx.reply(f"Set role react message to `{msg_id}` in <#{channel_id}>.")

    @Cog.command()
    async def sendmessage(self, ctx: fluxer.Message):
        """
        Send a message as the bot and configure it as the role reaction message.
        Usage: `!role sendmessage <text>`
        """
        if ctx.guild_id is None:
            await ctx.reply("This command can only be used in a server.")
            return

        if not await is_admin(self.bot, ctx):
            await ctx.reply("You need administrator permissions to use this command.")
            return

        text = ctx.content.split("sendmessage", 1)[-1].strip()
        if not text:
            await ctx.reply("Please provide the message text. Usage: `!role sendmessage <text>`")
            return

        if self.bot._http is None:
            await ctx.reply("HTTP client is not available.")
            return

        try:
            response = await self.bot._http.send_message(ctx.channel_id, content=text)
        except Exception as e:
            await ctx.reply(f"Failed to send message: {e}")
            return

        msg_id = int(response["id"])
        set_configured_message(ctx.guild_id, ctx.channel_id, msg_id)
        await ctx.reply(f"Sent and configured as the role react message (`{msg_id}`).")

    @Cog.command()
    async def removemessage(self, ctx: fluxer.Message):
        """
        Removes the configured role reaction message for the server.
        """
        if ctx.guild_id is None:
            await ctx.reply("This command can only be used in a server.")
            return

        if not await is_admin(self.bot, ctx):
            await ctx.reply("You need administrator permissions to use this command.")
            return

        if get_configured_message(ctx.guild_id) is None:
            await ctx.reply("No role react message is configured for this server.")
            return

        delete_configured_message_id(ctx.guild_id)
        await ctx.reply("Removed the role react message configuration.")


async def setup(bot: fluxer.Bot):
    await bot.add_cog(Admin(bot))
