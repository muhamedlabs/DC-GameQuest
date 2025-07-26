from disnake.ext import commands
from .button_click_1 import CustomOnButtonClick



def setup(bot: commands.Bot):
    bot.add_cog(CustomOnButtonClick(bot))
