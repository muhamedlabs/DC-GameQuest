from disnake.ext import commands
from .bot import BotBan
from .automod import AutoMod
from .scam import ScamVerification



def setup(bot: commands.Bot):
    bot.add_cog(BotBan(bot))
    bot.add_cog(AutoMod(bot))
    bot.add_cog(ScamVerification(bot))
