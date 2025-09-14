import disnake
from disnake.ext import commands
from .music import MusicPlayer
from .interaction import MusicIntegration
from .voicemode import VoiceControl
from .session import VoiceSessionTracker
from .random import RoomSelector


def setup(bot: commands.Bot):
    bot.add_cog(MusicPlayer(bot))
    bot.add_cog(MusicIntegration(bot))
    bot.add_cog(VoiceControl(bot))
    bot.add_cog(VoiceSessionTracker(bot))
    bot.add_cog(RoomSelector(bot))