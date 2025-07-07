import disnake
from disnake.ext import commands
import os

from BANNED_FILES.config import GREETING_CHANNEL_ID, MAIN_ROLE_ID, Welcome_Gif, Embed_Color


class WelcomeHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        role = member.guild.get_role(MAIN_ROLE_ID)
        if role:
            await member.add_roles(role, reason="Присоединился к серверу")

        welcome_channel = self.bot.get_channel(GREETING_CHANNEL_ID)
        if not welcome_channel:
            return

        if not os.path.isfile(Welcome_Gif):
            print(f"[ERROR] GIF-файл '{Welcome_Gif}' не найден.")
            return

        embed = disnake.Embed(
            title=f"<:enhance:1390972267504210062> Здравия желаю, {member.display_name}",
            description=(
                "Обязательно **ознакомьтесь** с правилами сервера, чтобы не пропустить важную информацию. "
                "**Исследуйте** разделы навигации для **поиска** дополнительного увлекательного контента.\n\n"
                "> Также, не упустите возможность **познакомиться** с другими участниками — за каждым никнеймом таится своя уникальная **история** и интересы!"
            ),
            color=self.embed_color
        )
        embed.set_image(url=f"attachment://{os.path.basename(Welcome_Gif)}")
        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

        with open(Welcome_Gif, "rb") as f:
            gif_file = disnake.File(f, filename=os.path.basename(Welcome_Gif))
            await welcome_channel.send(
                content=f"||{member.mention}||",
                embed=embed,
                file=gif_file
            )
