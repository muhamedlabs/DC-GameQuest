import disnake
from disnake.ext import commands
from BANNED_FILES.config import Embed_Color


def build_banner_embed(embed_color: disnake.Color, scope: str, display_name: str, banner_url: str | None, found: bool = True) -> disnake.Embed:
    if found:
        description = (
            "> Разведка **получила доступ** к центральному архиву и **извлекла** личное досье бойца.\n\n"
            f"Перед вами **{scope} банер** — официальный боевой **профиль военнослужащего**, зафиксированный в штабной системе"
        )
    else:
        description = (
            "> Разведка **получила доступ** к центральному архиву и **извлекла** личное досье бойца.\n\n"
            f"У бойца отсутствует **{scope} банер** в основном досье. Система активировала **резервный** визуальный профиль"
        )

    embed = disnake.Embed(
        title=f"<:taguser:1390972104295579688> Боевой флаг — **{display_name}**",
        description=description,
        color=embed_color
    )
    if banner_url:
        embed.set_image(url=banner_url)
    return embed


class BannerView(disnake.ui.View):
    def __init__(self, target_user: disnake.User, target_member: disnake.Member | None):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.target_member = target_member
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @disnake.ui.button(label="Глобальный банер", style=disnake.ButtonStyle.success, custom_id="global_banner")
    async def global_banner_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        fetched_user = await interaction.client.fetch_user(self.target_user.id)
        display_name = self.target_member.display_name if self.target_member else fetched_user.name

        if fetched_user.banner:
            embed = build_banner_embed(self.embed_color, "глобальный", display_name, fetched_user.banner.url, found=True)
        else:
            embed = build_banner_embed(self.embed_color, "глобального", display_name, None, found=False)

        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="Серверный банер", style=disnake.ButtonStyle.success, custom_id="server_banner")
    async def server_banner_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        fetched_member = None
        if interaction.guild and self.target_member:
            fetched_member = await interaction.guild.fetch_member(self.target_member.id)

        if fetched_member and fetched_member.guild_banner:
            embed = build_banner_embed(
                self.embed_color, "серверный", fetched_member.display_name,
                fetched_member.guild_banner.url, found=True
            )
        else:
            fetched_user = await interaction.client.fetch_user(self.target_user.id)
            display_name = fetched_member.display_name if fetched_member else fetched_user.name
            banner_url = fetched_user.banner.url if fetched_user.banner else None
            embed = build_banner_embed(self.embed_color, "серверного", display_name, banner_url, found=False)

        await interaction.response.edit_message(embed=embed, view=self)


class BannerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(name="флаг", description="Боевой флаг (банер) лейтенанта")
    async def banner(
        self,
        inter: disnake.AppCmdInter,
        target_user: disnake.User = commands.Param(
            name="пользователь", description="Участник сервера или пользователь Discord", default=None
        )
    ):
        target_user = target_user or inter.author
        target_member = inter.guild.get_member(target_user.id) if inter.guild else None

        fetched_member = await inter.guild.fetch_member(target_user.id) if inter.guild else None
        fetched_user = await self.bot.fetch_user(target_user.id)
        display_name = target_member.display_name if target_member else fetched_user.name

        if fetched_member and fetched_member.guild_banner:
            embed = build_banner_embed(
                self.embed_color, "серверный", fetched_member.display_name,
                fetched_member.guild_banner.url, found=True
            )
        else:
            banner_url = fetched_user.banner.url if fetched_user.banner else None
            embed = build_banner_embed(self.embed_color, "серверного", display_name, banner_url, found=False)

        view = BannerView(target_user, target_member)
        await inter.response.send_message(embed=embed, view=view)
