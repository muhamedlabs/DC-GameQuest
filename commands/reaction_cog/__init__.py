from disnake.ext import commands
from .music import ReactionMusic
from .youtube import ReactionYouTube
from .telegram import ReactionTelegram
from .chat import RandomReactor
from .administration import ReactionAdmin
from .operator import ReactionTracker



def setup(bot: commands.Bot):
    bot.add_cog(ReactionMusic(bot))
    bot.add_cog(ReactionYouTube(bot))
    bot.add_cog(ReactionTelegram(bot))
    bot.add_cog(RandomReactor(bot))
    bot.add_cog(ReactionAdmin(bot))
    bot.add_cog(ReactionTracker(bot))
