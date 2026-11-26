from fluxer import Cog

from logging import getLogger

import fluxer

logger = getLogger(__name__)


class Util(Cog):
    def __init__(self, bot: fluxer.Bot):
        super().__init__(bot)

    @Cog.command()
    async def ping(self, ctx: fluxer.Message):
        """
        A simple command to check if the bot is responsive. Replies with "Pong!" when invoked.
        """
        await ctx.reply("Pong!")

    @Cog.command()
    async def help(self, ctx: fluxer.Message):
        """
        A simple help command that lists available commands and their descriptions.
        """

        prefix = self.bot.command_prefix

        help_message = (
            "**Available Commands:**\n"
            f"`{prefix}ping` - Check if the bot is responsive.\n"
            f"`{prefix}help` - Display this help message.\n"
            f"`{prefix}sendmessage <text>` - Send a message as the bot and set it as a role react message (admin only).\n"
            f"`{prefix}setmessage <message_link>` - Set an existing message as a role react message (admin only).\n"
            f"`{prefix}add @Role <emoji>` - Add a role reaction to the most recent message (admin only).\n"
            f"`{prefix}remove <emoji>` - Remove a role reaction from the most recent message (admin only).\n"
            f"`{prefix}removemessage [message_link]` - Remove a role react message and its associations (admin only).\n"
        )
        await ctx.reply(help_message)


async def setup(bot: fluxer.Bot):
    await bot.add_cog(Util(bot))
