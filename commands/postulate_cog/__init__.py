from disnake.ext import commands
from .voice import AutoVoiceInfo



def setup(bot: commands.Bot):
    bot.add_cog(AutoVoiceInfo(bot))
