import asyncio
from disnake.ext import commands
import disnake

from BANNED_FILES.config import Embed_Color, GROUP_MODER_IDS, ALLOWED_USER_IDS

from commands.information_cog.warnings import no_access_embed, system_error_embed, critical_error_embed
from commands.information_cog.time import hours_time


class MessagePerson(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(
            name="message", 
            description="Отправить сообщение от имени бота"
    )

    @commands.contexts(bot_dm=False, guild=True)
    @commands.default_member_permissions(manage_messages=True, moderate_members=True, administrator=True)

    async def send(
        self,
        inter: disnake.ApplicationCommandInteraction,
        text: str = commands.Param(name="текст", description="Текст сообщения"),
        target_type: str = commands.Param(name="тип", choices=["канал", "пользователь"], description="Куда отправить"),
        target_id: str = commands.Param(name="айди", default=None, description="ID канала или пользователя"),
    ):
        owner = inter.guild.owner.mention if inter.guild and inter.guild.owner else "Не назначен"
        admins_mentions = " ".join(f"<@{uid}>" for uid in ALLOWED_USER_IDS)

        if not any(role.id in GROUP_MODER_IDS for role in inter.author.roles):
            await inter.response.send_message(
                embed=no_access_embed(self.embed_color, owner),
                ephemeral=True,
            )
            return

        if target_type == "канал":
            if not target_id:
                await inter.response.send_message(embed=system_error_embed(self.embed_color, owner), ephemeral=True)
                return

            channel = self.bot.get_channel(int(target_id))
            if channel is None:
                await inter.response.send_message(embed=system_error_embed(self.embed_color, owner), ephemeral=True)
                return

            await channel.send(text)
            embed = disnake.Embed(
                title="<:directbox:1534949116948250774> Сообщение отправлено в канал связи",
                description=(
                    f"> Сообщения передана по официальному каналу связи штаба. Сообщение зафиксировано и доставлено без задержек и потерь.\n\n"
                    f"<:usersquare:1534961881645580350> **Отправил лейтенант:** {inter.author.mention}\n"
                    f"<:directbox:1534949116948250774> **Канал назначения:** {channel.mention}\n"
                    f"<:calendar:1390972430780203058> **Время отправки:** {hours_time}"
                ),
                color=self.embed_color,
            )
            await inter.response.send_message(embed=embed, ephemeral=False)
            return

        if target_id:
            try:
                user = await self.bot.fetch_user(int(target_id))
            except (disnake.NotFound, ValueError):
                await inter.response.send_message(embed=system_error_embed(self.embed_color, owner), ephemeral=True)
                return

            try:
                await user.send(text)
            except (disnake.Forbidden, disnake.HTTPException):
                await inter.response.send_message(embed=critical_error_embed(self.embed_color, admins_mentions), ephemeral=True)
                return

            embed = disnake.Embed(
                title="<:directbox:1534949116948250774> Сообщение отправлено бойцу",
                description=(
                    f"> Личное сообщения доставлена бойцу в его канал связи. Штаб подтверждает получение адресатом.\n\n"
                    f"<:usersquare:1534961881645580350> **Отправил лейтенант:** {inter.author.mention}\n"
                    f"<:messagetick:1534949123030257966> **Получатель боец:** {user.mention}\n"
                    f"<:calendar:1390972430780203058> **Время отправки:** {hours_time}"
                ),
                color=self.embed_color,
            )
            await inter.response.send_message(embed=embed, ephemeral=False)
            return

        await inter.response.defer(ephemeral=True)
        members = [m for m in inter.guild.members if not m.bot]
        total = len(members)
        sent = 0
        skipped = 0

        progress_embed = disnake.Embed(
            title="<:directbox:1534949116948250774> Массовая рассылка личному составу началась",
            description=(
                f"> Операция активна. Выполняется рассылка всему личному составу штаба. Сообщения поочерёдно доставляются каждому бойцу гарнизона, штаб ведёт учёт доставленных и пропущенных сообщений в реальном времени.\n\n"
                f"<:usersquare:1534961881645580350> **Отправил лейтенант:** {inter.author.mention}\n"
                f"<:messagetick:1534949123030257966> **Доставлено бойцов:** 0\n"
                f"<:messageremove:1534949118584291600> **Пропущено бойцов:** 0\n\n"
                f"<:calendar:1390972430780203058> **Время выполнения задания:** {hours_time}"
            ),
            color=self.embed_color,
        )
        progress_msg = await inter.followup.send(embed=progress_embed, ephemeral=False)

        for i, member in enumerate(members, start=1):
            try:
                await member.send(text)
                sent += 1
            except disnake.HTTPException as e:
                if e.status == 429:
                    retry_after = getattr(e, "retry_after", 1) or 1
                    await asyncio.sleep(retry_after)
                    try:
                        await member.send(text)
                        sent += 1
                    except (disnake.Forbidden, disnake.HTTPException):
                        skipped += 1
                else:
                    skipped += 1
            except disnake.Forbidden:
                skipped += 1

            if i % 15 == 0 or i == total:
                progress_embed.description = (
                    f"> Операция активна. Выполняется рассылка всему личному составу штаба. Сообщения поочерёдно доставляются каждому бойцу гарнизона, штаб ведёт учёт доставленных и пропущенных сообщений в реальном времени.\n\n"
                    f"<:usersquare:1534961881645580350> **Отправил лейтенант:** {inter.author.mention}\n"
                    f"<:messagetick:1534949123030257966> **Доставлено бойцов:** {sent}\n"
                    f"<:messageremove:1534949118584291600> **Пропущено бойцов:** {skipped}\n\n"
                    f"<:calendar:1390972430780203058> **Время выполнения задания:** {hours_time}"
                )
                await progress_msg.edit(embed=progress_embed)

            await asyncio.sleep(1)

        final_embed = disnake.Embed(
            title="<:directbox:1534949116948250774> Массовая рассылка личному составузавершена",
            description=(
                f"> Операция завершена. Сообщения разосланы всему личному составу гарнизона, штаб закрывает задание и переходит к следующей операции.\n\n"
                f"<:usersquare:1534961881645580350> **Отправил лейтенант:** {inter.author.mention}\n"
                f"<:messagetick:1534949123030257966> **Доставлено бойцов:** {sent}\n"
                f"<:messageremove:1534949118584291600> **Пропущено бойцов:** {skipped}\n\n"
                f"<:calendar:1390972430780203058> **Время выполнения задания:** {hours_time}"
            ),
            color=self.embed_color,
        )
        await progress_msg.edit(embed=final_embed)
