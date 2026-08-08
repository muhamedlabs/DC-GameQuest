from disnake.ext import commands
from .video import VideoIntegration
from .webhook import WebhookFromDiscord
from .message import MessagePerson



def setup(bot: commands.Bot):
    bot.add_cog(VideoIntegration(bot))
    bot.add_cog(WebhookFromDiscord(bot))
    bot.add_cog(MessagePerson(bot))
