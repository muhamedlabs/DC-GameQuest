from disnake.ext import commands
from .greeting import GreetingResponder
from .handler import WelcomeHandler



def setup(bot: commands.Bot):
    bot.add_cog(GreetingResponder(bot))
    bot.add_cog(WelcomeHandler(bot))
