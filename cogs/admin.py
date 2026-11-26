# cogs/admin.py
import fluxer
from fluxer import Cog
from urllib.parse import urlparse

from util.admin import is_admin
from util.database import (
    count_role_associations,
    delete_configured_message,
    get_configured_messages,
    get_latest_configured_message,
    is_configured_message,
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
            try:
                await ctx.reply(embed=make_embed(f"Failed to send message: {e}"))
            except Exception:
                await ctx.reply(f"Failed to send message: {e}")
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

        # Accept a message link, a raw message ID, or nothing (defaults to latest).
        words = ctx.content.split()
        arg = words[-1] if len(words) > 1 else None

        if arg is not None and "channels/" in arg:
            result = parse_message_link(arg, ctx.guild_id)
            if isinstance(result, str):
                await ctx.reply(embed=make_embed(result))
                return
            _, msg_id = result
        elif arg is not None and arg.isdigit():
            msg_id = int(arg)
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


    @Cog.command()
    async def listmessages(self, ctx: fluxer.Message):
        """List all configured role reaction messages for the server."""
        if ctx.guild_id is None:
            await ctx.reply(embed=make_embed("This command can only be used in a server."))
            return

        if not await is_admin(self.bot, ctx):
            await ctx.reply(embed=make_embed("You need administrator permissions to use this command."))
            return

        messages = get_configured_messages(ctx.guild_id)
        if not messages:
            await ctx.reply(embed=make_embed("No role react messages are configured for this server."))
            return

        lines = ["**Configured role react messages:**\n"]
        for i, msg in enumerate(messages, 1):
            roles_count = count_role_associations(ctx.guild_id, msg["message_id"])
            lines.append(
                f"{i}. `{msg['message_id']}` in <#{msg['channel_id']}> — {roles_count} role(s)"
            )

        await ctx.reply(embed=make_embed("\n".join(lines)))

    @Cog.command()
    async def editmessage(self, ctx: fluxer.Message):
        """
        Edit the text of a configured bot message.
        With a link: edits that message.
        Without a link: edits the most recently configured message.
        """
        if ctx.guild_id is None:
            await ctx.reply(embed=make_embed("This command can only be used in a server."))
            return

        if not await is_admin(self.bot, ctx):
            await ctx.reply(embed=make_embed("You need administrator permissions to use this command."))
            return

        if self.bot._http is None:
            await ctx.reply(embed=make_embed("HTTP client is not available."))
            return

        # Split content after the command name.
        after_cmd = ctx.content.split("editmessage", 1)[-1].strip()
        if not after_cmd:
            await ctx.reply(embed=make_embed("Usage: `editmessage [message_link] <new text>`"))
            return

        # Check if the first word is a message link.
        first_word = after_cmd.split()[0]
        if "channels/" in first_word:
            result = parse_message_link(first_word, ctx.guild_id)
            if isinstance(result, str):
                await ctx.reply(embed=make_embed(result))
                return
            channel_id, msg_id = result
            new_text = after_cmd[len(first_word):].strip()
        else:
            configured = get_latest_configured_message(ctx.guild_id)
            if configured is None:
                await ctx.reply(embed=make_embed("No role react message is configured."))
                return
            channel_id = configured["channel_id"]
            msg_id = configured["message_id"]
            new_text = after_cmd

        if not new_text:
            await ctx.reply(embed=make_embed("Please provide the new message text."))
            return

        if not is_configured_message(ctx.guild_id, msg_id):
            await ctx.reply(embed=make_embed("That message is not configured as a role react message."))
            return

        try:
            await self.bot._http.edit_message(
                channel_id, msg_id, embeds=[make_embed(new_text)]
            )
        except Exception as e:
            try:
                await ctx.reply(embed=make_embed(f"Failed to edit message: {e}"))
            except Exception:
                await ctx.reply(f"Failed to edit message: {e}")
            return

        await ctx.reply(embed=make_embed(f"Updated message `{msg_id}`."))


async def setup(bot: fluxer.Bot):
    await bot.add_cog(Admin(bot))
