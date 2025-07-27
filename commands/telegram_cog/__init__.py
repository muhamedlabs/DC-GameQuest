from disnake.ext import commands
from .telegram import TelegramBridge


def setup(bot: commands.Bot):
    bot.add_cog(TelegramBridge(bot))
