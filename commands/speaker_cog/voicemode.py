import disnake
from disnake.ext import commands
from datetime import datetime, timedelta
from BANNED_FILES.config import Embed_Color, GROUP_ADMIN_ID, SPEAKER_VOICE_ID, Speechify_Image


class VoiceControl(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    def channel_mention(self, ch: disnake.abc.GuildChannel) -> str:
        return f"<#{ch.id}>" if ch else "—"

    @commands.slash_command(
        name="bot_voice",
        description="Управление голосовой связью с сержантом",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_messages=True)
    )
    async def voice(
        self,
        inter: disnake.ApplicationCommandInteraction,
        действие: str = commands.Param(
            choices=["Загнать", "Выгнать"],
            description="Приказ для сержанта"
        )
    ):
        # Проверка доступа по ролям
        has_access = (
            any(role.id in GROUP_ADMIN_ID for role in inter.author.roles)
            if isinstance(GROUP_ADMIN_ID, list)
            else any(role.id == GROUP_ADMIN_ID for role in inter.author.roles)
        )
        if not has_access:
            embed = disnake.Embed(
                title="<:forbidden:1390972224436965386> Доступ к команде заблокирован",
                description=(
                    "У вас **отсутствуют полномочия** для выполнения данного приказа.\n\n"
                    f">>> Если вы считаете, что это ошибка — свяжитесь с адмиралом базы: {inter.guild.owner.mention}"
                ),
                color=self.embed_color
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        await inter.response.defer(ephemeral=True)

        voice_channel = inter.guild.get_channel(SPEAKER_VOICE_ID)
        if not voice_channel or not isinstance(voice_channel, disnake.VoiceChannel):
            await inter.edit_original_response(
                content=f"Канал с ID `{SPEAKER_VOICE_ID}` не найден или это не голосовой канал!"
            )
            return

        file = disnake.File(Speechify_Image, filename="vocast.png")

        music_player = self.bot.get_cog("MusicPlayer")
        if not music_player:
            await inter.edit_original_response(content="Модуль MusicPlayer не загружен.")
            return

        if действие == "Загнать":
            # Очистка последних 5 сообщений, кроме закрепленных
            text_channel = inter.channel
            if isinstance(text_channel, disnake.TextChannel):
                try:
                    await text_channel.purge(limit=5, check=lambda m: not m.pinned)
                except Exception:
                    pass  # Игнорируем ошибки очистки

            # Запускаем подключение и воспроизведение музыки асинхронно, не блокируя обработчик
            self.bot.loop.create_task(music_player.connect_and_play())

            moscow_time = (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

            embed = disnake.Embed(
                title="<:callcalling:1390972394268659753> Сержант подключился к сети",
                description=(
                    f"> Голосовая связь **установлена** по приказу: {inter.author.mention}. "
                    f"Операция в полном разгаре, связь **стабильна** и под контролем штаба.\n\n"
                    f"<:channel:1390972349385281630> **Сектор:** {self.channel_mention(voice_channel)}\n"
                    f"<:calendar:1390972430780203058> **Время подключения:** {moscow_time} по МСК"
                ),
                color=self.embed_color
            )
            embed.set_image(url="attachment://vocast.png")
            embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
            await inter.edit_original_response(embed=embed, file=file)

        elif действие == "Выгнать":
            if music_player.voice_client:
                try:
                    await music_player.force_disconnect()
                except Exception as e:
                    await inter.edit_original_response(content=f"Ошибка при отключении от голосового канала: {e}")
                    return

                moscow_time = (datetime.utcnow() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')

                embed = disnake.Embed(
                    title="<:callslash:1390972370508054578> Сержант покинул сектор",
                    description=(
                        f"> Голосовая связь **разорвана** по приказу: {inter.author.mention}. "
                        f"Линия молчит, миссия окончена. **Ожидаем** новых распоряжений штаба.\n\n"
                        f"<:channel:1390972349385281630> **Сектор:** {self.channel_mention(voice_channel)}\n"
                        f"<:calendar:1390972430780203058> **Время отключения:** {moscow_time} по МСК"
                    ),
                    color=self.embed_color
                )
                embed.set_image(url="attachment://vocast.png")
                embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
                await inter.edit_original_response(embed=embed, file=file)
            else:
                await inter.edit_original_response(content="Бот не подключён ни к одному голосовому каналу.")
