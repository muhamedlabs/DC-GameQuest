import disnake
from disnake.ext import commands
import os
from commands.information_cog.warnings import (
    no_access_embed,
)
from BANNED_FILES.config import Embed_Color, Assembly_Gif


class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(
        name="сервер",
        description="Сканирование серверной инфраструктуры"
    )
    async def serverinfo(self, inter: disnake.AppCmdInter):
        await inter.response.defer()

        if not inter.guild:
            owner = "Администратор"
            embed = no_access_embed(self.embed_color, owner)

            await inter.edit_original_response(embed=embed, ephemeral=True)
            return

        guild = await self.bot.fetch_guild(inter.guild_id, with_counts=True)
        cached = inter.guild

        try:
            owner_user = await self.bot.fetch_user(guild.owner_id)
            commander = owner_user.mention
        except Exception:
            commander = "Неизвестно"

        created = guild.created_at.strftime("%d.%m.%Y")
        server_id = guild.id

        description = guild.description or "📡 Назначение и цели объекта: засекречены."

        total_members = guild.approximate_member_count or "—"
        online_members = guild.approximate_presence_count or "—"

        text_channels = len(cached.text_channels)
        voice_channels = len(cached.voice_channels)
        roles = len(cached.roles)
        categories = len(cached.categories)
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count or 0

        embed = disnake.Embed(
            title=f"<:courthouse:1388889492865155153> Картирование инфраструктуры {guild.name}",
            description=(
                "> Оперативный отчёт о боеспособности подразделения.\n\n"
                f"<:usersquar:1388889541645172957> **Адмирал базы:** {commander}\n"
                f"<:calendar2:1388889677297352837> **Дата основания:** `{created}`\n"
                f"<:driver:1388889638256644189> **Индикатор базы:** `{server_id}`\n\n"
                f"<:textalign:1388889563640103032> **Описание базы:**\n```{description}```\n"
                f"<:people:1388889582354960608> **Личный состав:** `Всего: {total_members}` | `Активны: {online_members}`\n"
                f"<:char:1388889657906827395> **Каналы:** `Текст: {text_channels}` | `Голос: {voice_channels}`\n"
                f"<:graph:1388889597882269717> **Структура:** `Ролей: {roles}` | `Категорий: {categories}`\n"
                f"<:flash:1388889612818186250> **Поддержка:** `Уровень: {boost_level}` | `Бустов: {boost_count}`"
            ),
            color=self.embed_color
        )

        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

        gif_path = Assembly_Gif

        if os.path.exists(gif_path):
            file = disnake.File(gif_path, filename="military.gif")
            embed.set_image(url="attachment://military.gif")
            await inter.edit_original_response(embed=embed, file=file)
        else:
            await inter.edit_original_response(embed=embed)