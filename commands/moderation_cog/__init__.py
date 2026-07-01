from disnake.ext import commands
from .bot import BotBan
from .automod import AutoMod



def setup(bot: commands.Bot):
    bot.add_cog(BotBan(bot))
    bot.add_cog(AutoMod(bot))
