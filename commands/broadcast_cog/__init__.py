import disnake
from disnake.ext import commands
from .privat import PrivateVoiceManager
from .controller import VoiceAutoMover



def setup(bot: commands.Bot):
    bot.add_cog(PrivateVoiceManager(bot))
    bot.add_cog(VoiceAutoMover(bot))
