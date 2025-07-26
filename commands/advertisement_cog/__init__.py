from disnake.ext import commands
from .promo import AutoPromo


def setup(bot: commands.Bot):
    bot.add_cog(AutoPromo(bot))

