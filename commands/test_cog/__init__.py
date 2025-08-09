import disnake
from disnake.ext import commands
from .text import TextCommands



def setup(bot: commands.Bot):
    bot.add_cog(TextCommands(bot))
