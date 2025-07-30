from disnake.ext import commands
from .video import VideoIntegration



def setup(bot: commands.Bot):
    bot.add_cog(VideoIntegration(bot))
