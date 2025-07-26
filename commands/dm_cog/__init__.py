from disnake.ext import commands
from .responder import DMResponder
from .notification import FirstNotifier


def setup(bot: commands.Bot):
    bot.add_cog(DMResponder(bot))
    bot.add_cog(FirstNotifier(bot))
