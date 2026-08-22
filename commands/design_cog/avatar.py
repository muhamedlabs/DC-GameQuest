import disnake
from disnake.ext import commands
from BANNED_FILES.config import Embed_Color


def build_avatar_embed(embed_color: disnake.Color, scope: str, display_name: str, avatar_url: str, found: bool = True) -> disnake.Embed:
    if found:
        description = (
            "> Разведка **получила доступ** к центральному архиву и **извлекла** личное досье бойца.\n\n"
            f"Перед вами **{scope} аватар** — официальный боевой **профиль военнослужащего**, зафиксированный в штабной системе"
        )
    else:
        description = (
            "> Разведка **получила доступ** к центральному архиву и **извлекла** личное досье бойца.\n\n"
            f"У бойца отсутствует **{scope} аватар** в основном досье. Система активировала **резервный** визуальный профиль"
        )

    embed = disnake.Embed(
        title=f"<:taguser:1390972104295579688> Голограмма бойца — **{display_name}**",
        description=description,
        color=embed_color
    )
    embed.set_image(url=avatar_url)
    return embed


class AvatarView(disnake.ui.View):
    def __init__(self, target_user: disnake.User, target_member: disnake.Member | None):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.target_member = target_member
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @disnake.ui.button(label="Глобальный аватар", style=disnake.ButtonStyle.success, custom_id="global_avatar")
    async def global_avatar_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        avatar_url = self.target_user.avatar.url if self.target_user.avatar else self.target_user.default_avatar.url
        display_name = self.target_member.display_name if self.target_member else self.target_user.name

        embed = build_avatar_embed(self.embed_color, "глобальный", display_name, avatar_url, found=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="Серверный аватар", style=disnake.ButtonStyle.success, custom_id="server_avatar")
    async def server_avatar_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if self.target_member and self.target_member.display_avatar:
            embed = build_avatar_embed(
                self.embed_color, "серверный", self.target_member.display_name,
                self.target_member.display_avatar.url, found=True
            )
        else:
            avatar_url = self.target_user.avatar.url if self.target_user.avatar else self.target_user.default_avatar.url
            display_name = self.target_member.display_name if self.target_member else self.target_user.name
            embed = build_avatar_embed(self.embed_color, "серверного", display_name, avatar_url, found=False)

        await interaction.response.edit_message(embed=embed, view=self)


class AvatarCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(name="голограмма", description="Боевая голограмма (аватарка) лейтенанта")
    async def avatar(
        self,
        inter: disnake.AppCmdInter,
        target_user: disnake.User = commands.Param(
            name="пользователь", description="Участник сервера или пользователь Discord", default=None
        )
    ):
        target_user = target_user or inter.author
        target_member = inter.guild.get_member(target_user.id) if inter.guild else None

        if target_member and target_member.display_avatar:
            embed = build_avatar_embed(
                self.embed_color, "серверный", target_member.display_name,
                target_member.display_avatar.url, found=True
            )
        else:
            avatar_url = target_user.avatar.url if target_user.avatar else target_user.default_avatar.url
            display_name = target_member.display_name if target_member else target_user.name
            embed = build_avatar_embed(self.embed_color, "серверного", display_name, avatar_url, found=False)

        view = AvatarView(target_user, target_member)
        await inter.response.send_message(embed=embed, view=view)
