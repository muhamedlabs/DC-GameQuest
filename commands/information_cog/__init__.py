import disnake
from disnake.ext import commands
from .server import ServerInfo
from .broadcast import LanguageInfo
from .renewal import Updates


def setup(bot: commands.Bot):
    bot.add_cog(ServerInfo(bot))
    bot.add_cog(LanguageInfo(bot))
    bot.add_cog(Updates(bot))
    