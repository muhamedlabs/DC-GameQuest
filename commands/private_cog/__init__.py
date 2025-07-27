import disnake
from disnake.ext import commands
from .voice import PrivateVoiceManager



def setup(bot: commands.Bot):
    bot.add_cog(PrivateVoiceManager(bot))
