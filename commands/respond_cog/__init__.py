import disnake
from disnake.ext import commands
from .visas import ResponseToCall
from .reaction import MentionResponse


def setup(bot: commands.Bot):
    bot.add_cog(MentionResponse(bot))
    bot.add_cog(ResponseToCall(bot))
