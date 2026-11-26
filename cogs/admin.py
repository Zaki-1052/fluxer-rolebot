# cogs/admin.py
import fluxer
from fluxer import Cog
from urllib.parse import urlparse

from util.admin import is_admin
from util.database import (
    delete_configured_message,
    get_latest_configured_message,
    set_configured_message,
)
from util.embed import make_embed
import logging

logger = logging.getLogger(__name__)


def parse_message_link(text: str, expected_guild_id: int) -> tuple[int, int] | str:
    """Parse a message link and return (channel_id, message_id) or an error string."""
    parsed_link = urlparse(text)
    if not parsed_link.path:
        return "Invalid message link format."

    split_path = parsed_link.path.split("/")
    if len(split_path) < 5 or split_path[-4] != "channels":
        return "Invalid message link format."

    try:
        guild_id = int(split_path[-3])
        channel_id = int(split_path[-2])
        msg_id = int(split_path[-1])
    except ValueError:
        return "Invalid message link format."

    if guild_id != expected_guild_id:
        return "The linked message must be in the same server."

    return (channel_id, msg_id)


class Admin(Cog):
    def __init__(self, bot: fluxer.Bot):
        super().__init__(bot)

    @Cog.command()
    async def setmessage(self, ctx: fluxer.Message):
        """
        Configure an existing message as a role reaction message.
        Usage: `!role setmessage <message_link>`
        Multiple messages per server are supported.
        """
        if ctx.guild_id is None:
            await ctx.reply(embed=make_embed("This command can only be used in a server."))
            return

        if not await is_admin(self.bot, ctx):
            await ctx.reply(embed=make_embed("You need administrator permissions to use this command."))
            return

        result = parse_message_link(ctx.content.split()[-1], ctx.guild_id)
        if isinstance(result, str):
            await ctx.reply(embed=make_embed(result))
            return

        channel_id, msg_id = result
        set_configured_message(ctx.guild_id, channel_id, msg_id)
        await ctx.reply(embed=make_embed(f"Set role react message to `{msg_id}` in <#{channel_id}>."))

    @Cog.command()
    async def sendmessage(self, ctx: fluxer.Message):
        """
        Send a message as the bot and configure it as a role reaction message.
        Usage: `!role sendmessage <text>`
        """
        if ctx.guild_id is None:
            await ctx.reply(embed=make_embed("This command can only be used in a server."))
            return

        if not await is_admin(self.bot, ctx):
            await ctx.reply(embed=make_embed("You need administrator permissions to use this command."))
            return

        text = ctx.content.split("sendmessage", 1)[-1].strip()
        if not text:
            await ctx.reply(embed=make_embed("Please provide the message text. Usage: `!role sendmessage <text>`"))
            return

        if self.bot._http is None:
            await ctx.reply(embed=make_embed("HTTP client is not available."))
            return

        try:
            response = await self.bot._http.send_message(ctx.channel_id, embed=make_embed(text))
        except Exception as e:
            await ctx.reply(embed=make_embed(f"Failed to send message: {e}"))
            return

        msg_id = int(response["id"])
        set_configured_message(ctx.guild_id, ctx.channel_id, msg_id)
        await ctx.reply(embed=make_embed(f"Sent and configured as the role react message (`{msg_id}`)."))

    @Cog.command()
    async def removemessage(self, ctx: fluxer.Message):
        """
        Remove a configured role reaction message and its role associations.
        With a message link: removes that specific message.
        Without a link: removes the most recently configured message.
        """
        if ctx.guild_id is None:
            await ctx.reply(embed=make_embed("This command can only be used in a server."))
            return

        if not await is_admin(self.bot, ctx):
            await ctx.reply(embed=make_embed("You need administrator permissions to use this command."))
            return

        # Check if a message link was provided.
        words = ctx.content.split()
        link_word = words[-1] if len(words) > 1 else None
        has_link = link_word is not None and "channels/" in link_word

        if has_link and link_word is not None:
            result = parse_message_link(link_word, ctx.guild_id)
            if isinstance(result, str):
                await ctx.reply(embed=make_embed(result))
                return
            _, msg_id = result
        else:
            configured = get_latest_configured_message(ctx.guild_id)
            if configured is None:
                await ctx.reply(embed=make_embed("No role react message is configured for this server."))
                return
            msg_id = configured["message_id"]

        if not delete_configured_message(ctx.guild_id, msg_id):
            await ctx.reply(embed=make_embed("That message is not configured as a role react message."))
            return

        await ctx.reply(embed=make_embed(f"Removed role react message `{msg_id}` and its role associations."))


async def setup(bot: fluxer.Bot):
    await bot.add_cog(Admin(bot))
