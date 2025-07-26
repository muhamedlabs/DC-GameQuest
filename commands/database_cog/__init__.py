from disnake.ext import commands
from .synchronize import Sync



def setup(bot: commands.Bot):
    bot.add_cog(Sync(bot))
