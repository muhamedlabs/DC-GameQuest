from disnake.ext import commands
from .button_click_1 import CustomOnButtonClick
from .greeting_button import GreetingButton


def setup(bot: commands.Bot):
    bot.add_cog(CustomOnButtonClick(bot))
    bot.add_cog(GreetingButton(bot))