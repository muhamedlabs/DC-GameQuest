from disnake.ext import commands
from .pictures import Unsplash
from .ball import WarBall
from .games import GameOrders
from .translate import Translator


def setup(bot: commands.Bot):
    bot.add_cog(Unsplash(bot))
    bot.add_cog(WarBall(bot))
    bot.add_cog(GameOrders(bot))
    bot.add_cog(Translator(bot))
