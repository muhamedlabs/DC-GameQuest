from disnake.ext import commands
from .pictures import Unsplash
from .ball import WarBall


def setup(bot: commands.Bot):
    bot.add_cog(Unsplash(bot))
    bot.add_cog(WarBall(bot))
