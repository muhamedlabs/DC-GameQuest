import disnake
from disnake.ext import commands
from BANNED_FILES.config import Embed_Color


class AvatarView(disnake.ui.View):
    def __init__(self, user: disnake.User, member: disnake.Member | None):
        super().__init__(timeout=None)
        self.user = user
        self.member = member
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @disnake.ui.button(label="Глобальный аватар", style=disnake.ButtonStyle.success, custom_id="global_avatar")
    async def global_avatar_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        avatar_url = self.user.avatar.url if self.user.avatar else self.user.default_avatar.url
        description = "> За этим глобальным аватаром скрывается настоящий воин (или теран?)"
        name = self.member.display_name if self.member else self.user.name

        embed = disnake.Embed(
            title=f"<:taguser:1390972104295579688> Голограмма — {name}",
            description=description,
            color=self.embed_color
        )
        embed.set_image(url=avatar_url)
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="Серверный аватар", style=disnake.ButtonStyle.success, custom_id="server_avatar")
    async def server_avatar_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if self.member and self.member.display_avatar:
            avatar_url = self.member.display_avatar.url
            description = "> За этим серверным аватаром скрывается настоящий воин (или теран?)"
            name = self.member.display_name
        else:
            avatar_url = self.user.display_avatar.url
            description = "> Серверный аватар сбежал в космос? Не беда — глобальный всегда прикрывает спину!"
            name = self.user.name

        embed = disnake.Embed(
            title=f"<:taguser:1390972104295579688> Голограмма — {name}",
            description=description,
            color=self.embed_color
        )
        embed.set_image(url=avatar_url)
        await interaction.response.edit_message(embed=embed, view=self)


class AvatarCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(name="голограмма", description="Показать боевою голограмму пользователя")
    async def avatar(
        self,
        inter: disnake.AppCmdInter,
        пользователь: disnake.User = commands.Param(
            name="пользователь", description="Участник сервера или пользователь Discord", default=None
        )
    ):
        user = пользователь or inter.author
        member = inter.guild.get_member(user.id) if inter.guild else None

        if member and member.display_avatar:
            avatar_url = member.display_avatar.url
            description = "> За этим серверным аватаром скрывается настоящий воин (или теран?)"
            name = member.display_name
        else:
            avatar_url = user.display_avatar.url
            description = "> Серверный аватар сбежал в космос? Не беда — глобальный всегда прикрывает спину!"
            name = user.name

        embed = disnake.Embed(
            title=f"<:taguser:1390972104295579688> Голограмма — {name}",
            description=description,
            color=self.embed_color
        )
        embed.set_image(url=avatar_url)

        view = AvatarView(user, member)
        await inter.response.send_message(embed=embed, view=view)
