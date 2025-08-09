import disnake
from disnake.ext import commands
from .cleaning import CleanCommand
from .archive import AdsCommand
from .deletes import DeleteMessages


def setup(bot: commands.Bot):
    bot.add_cog(CleanCommand(bot))
    bot.add_cog(AdsCommand(bot))
    bot.add_cog(DeleteMessages(bot))

