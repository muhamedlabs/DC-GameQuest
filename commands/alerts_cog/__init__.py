import disnake
from disnake.ext import commands
from .signal import SignalSubscription
from .mailing import SignalSender



def setup(bot: commands.Bot):
    bot.add_cog(SignalSubscription(bot))
    bot.add_cog(SignalSender(bot))

