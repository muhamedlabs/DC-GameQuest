import disnake
from disnake.ext import commands
from BANNED_FILES.config import Embed_Color


class BannerView(disnake.ui.View):
    def __init__(self, user: disnake.User, member: disnake.Member | None, bot: commands.Bot):
        super().__init__(timeout=None)
        self.user = user
        self.member = member
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @disnake.ui.button(label="Серверный банер", style=disnake.ButtonStyle.success, custom_id="server_banner")
    async def server_banner_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        if not self.member or not interaction.guild:
            await interaction.response.send_message("Боец не найден на плацдарме сервера.", ephemeral=True)
            return

        try:
            fetched_member = await interaction.guild.fetch_member(self.member.id)
        except Exception:
            await interaction.response.send_message("Не удалось захватить данные бойца.", ephemeral=True)
            return

        if fetched_member.banner:
            embed = disnake.Embed(
                title=f"<:taguser:1390972104295579688> Флагшток — {fetched_member.display_name}",
                description="> Этот серверный флагшток развевается в честь воина, готового к бою!",
                color=self.embed_color
            )
            embed.set_image(url=fetched_member.banner.url)
        else:
            # Если серверный баннер отсутствует, выводим глобальный — резервный флаг
            try:
                fetched_user = await self.bot.fetch_user(self.user.id)
            except Exception:
                await interaction.response.send_message("Не удалось получить данные командира.", ephemeral=True)
                return

            if fetched_user.banner:
                embed = disnake.Embed(
                    title=f"<:taguser:1390972104295579688> Флагшток — {fetched_user.display_name}",
                    description="> У бойца нет серверного флагштока, показываем его глобальный знак доблести!",
                    color=self.embed_color
                )
                embed.set_image(url=fetched_user.banner.url)
            else:
                embed = disnake.Embed(
                    title=f"<:taguser:1390972104295579688> Флагшток — {self.user.display_name}",
                    description="> У бойца нет знамени. Тишина на фронте.",
                    color=self.embed_color
                )
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(label="Глобальный банер", style=disnake.ButtonStyle.success, custom_id="global_banner")
    async def global_banner_button(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        try:
            fetched_user = await self.bot.fetch_user(self.user.id)
        except Exception:
            await interaction.response.send_message("Не удалось получить данные командира.", ephemeral=True)
            return

        if fetched_user.banner:
            embed = disnake.Embed(
                title=f"<:taguser:1390972104295579688> Флагшток — {fetched_user.display_name}",
                description="> Этот глобальный флагшток развевается над всем полем боя, символ чести и отваги!",
                color=self.embed_color
            )
            embed.set_image(url=fetched_user.banner.url)
        else:
            embed = disnake.Embed(
                title=f"<:taguser:1390972104295579688> Флагшток — {self.user.display_name}",
                description="> Боец без знамени, но с несломленным духом.",
                color=self.embed_color
            )
        await interaction.response.edit_message(embed=embed, view=self)


class BannerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(name="флагшток", description="Отобразить боевой флаг пользователя")
    async def banner(
        self,
        inter: disnake.AppCmdInter,
        пользователь: disnake.User = commands.Param(name="пользователь", description="Участник сервера или пользователь Discord", default=None)
    ):
        user = пользователь or inter.author
        member = None
        if inter.guild:
            try:
                member = await inter.guild.fetch_member(user.id)
            except Exception:
                member = None  # Если не удалось — просто None

        try:
            fetched_user = await self.bot.fetch_user(user.id)
        except Exception:
            embed = disnake.Embed(
                title="<:forbidden:1390972224436965386> Ошибка",
                description="> Не удалось получить разведданные о пользователе.",
                color=self.embed_color
            )
            await inter.response.send_message(embed=embed)
            return

        # По умолчанию — показываем глобальный флагшток командира
        if fetched_user.banner:
            embed = disnake.Embed(
                title=f"<:taguser:1390972104295579688> Флагшток — {fetched_user.display_name}",
                description="> Это глобальный боевой флаг пользователя, символ доблести!",
                color=self.embed_color
            )
            embed.set_image(url=fetched_user.banner.url)
        else:
            embed = disnake.Embed(
                title=f"<:taguser:1390972104295579688> Флагшток — {fetched_user.display_name}",
                description="> У бойца нет боевого знамени, но дух его не сломить!",
                color=self.embed_color
            )

        view = BannerView(user=fetched_user, member=member, bot=self.bot)
        await inter.response.send_message(embed=embed, view=view)

