import disnake
from disnake.ext import commands
import datetime
import os
import asyncio

from BANNED_FILES.config import Embed_Color

class MentionResponse(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot or not message.guild:
            return

        if self.bot.user.mentioned_in(message):
            embed = disnake.Embed(
                title="<:flash:1388889612818186250> Энергичное сообщение от сержанта",
                description=(
                    "> Сержант в настоящий момент **задействован** на ключевой операции. Связь **временно** прервана. Рапорт можно **передать** через личку и он дойдёт до штаба.\n\n"
                ),
                color=self.embed_color
            )

            embed.add_field(
                name="<:watchstatus:1388950489005166612> Позывной и данные по сержанту:",
                value="```!Game Quest``` ",
                inline=False
            )

            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)

            reply = await message.channel.send(embed=embed)
            await asyncio.sleep(35)
            try:
                await reply.delete()
            except disnake.NotFound:
                pass  # сообщение уже удалено вручную
