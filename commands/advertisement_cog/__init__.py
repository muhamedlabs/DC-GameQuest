from disnake.ext import commands
from .reminders import AutoPromo


def setup(bot: commands.Bot):
    bot.add_cog(AutoPromo(bot))
