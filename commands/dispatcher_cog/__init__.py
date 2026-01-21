from disnake.ext import commands
from .video import VideoIntegration
from .webhook import WebhookFromDiscord



def setup(bot: commands.Bot):
    bot.add_cog(VideoIntegration(bot))
    bot.add_cog(WebhookFromDiscord(bot))
