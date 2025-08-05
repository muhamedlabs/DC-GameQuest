import disnake
from disnake.ext import commands
from .activity import StatusBot
from .text import TextCommands
from .restart import ReloadAllCog


def setup(bot: commands.Bot):
    bot.add_cog(StatusBot(bot))
    bot.add_cog(TextCommands(bot))
    bot.add_cog(ReloadAllCog(bot))
