from disnake.ext import commands
from .video import VideoIntegration
from .voice import AutoVoiceInfo



def setup(bot: commands.Bot):
    bot.add_cog(VideoIntegration(bot))
    bot.add_cog(AutoVoiceInfo(bot))
