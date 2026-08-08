import disnake
from disnake.ext import commands
from datetime import datetime, timedelta
from BANNED_FILES.config import Embed_Color, GROUP_ADMIN_ID, ALLOWED_USER_IDS, Speechify_Image, RedisManager
from commands.information_cog.warnings import critical_error_embed, invalid_input_embed, no_access_embed
from commands.information_cog.time import hours_time
from redis_storage.speaker_voice import SpeakerVoice


class VoiceControl(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    async def get_voice_channel(self, guild: disnake.Guild) -> disnake.VoiceChannel | None:
        """Берём текущий канал из Redis по ключу 'random_channel' безопасно"""
        async with RedisManager() as redis:
            try:
                record = await redis.load(SpeakerVoice, key="random_channel")
            except Exception:
                return None

        if not record or not record.random_channel_id:
            return None

        channel = guild.get_channel(int(record.random_channel_id))
        if not isinstance(channel, disnake.VoiceChannel):
            return None
        return channel

    def channel_mention(self, ch: disnake.abc.GuildChannel) -> str:
        return f"<#{ch.id}>" if ch else "—"

    @commands.slash_command(
        name="bot_voice",
        description="Управление голосовой связью с сержантом",
    )
    @commands.contexts(bot_dm=False, guild=True)
    @commands.default_member_permissions(manage_messages=True, moderate_members=True, administrator=True)
    async def voice(
        self,
        inter: disnake.ApplicationCommandInteraction,
        действие: str = commands.Param(
            choices=["Загнать", "Выгнать"],
            description="Приказ для сержанта"
        )
    ):
        admins_mentions = " ".join(f"<@{uid}>" for uid in ALLOWED_USER_IDS)

        # Проверка доступа по ролям — ephemeral: True
        has_access = (
            any(role.id in GROUP_ADMIN_ID for role in inter.author.roles)
            if isinstance(GROUP_ADMIN_ID, list)
            else any(role.id == GROUP_ADMIN_ID for role in inter.author.roles)
        )
        if not has_access:
            await inter.response.send_message(
                embed=no_access_embed(self.embed_color, owner=inter.author),
                ephemeral=True
            )
            return

        voice_channel = await self.get_voice_channel(inter.guild)
        music_player = self.bot.get_cog("MusicPlayer")

        # Канал не найден в Redis — ephemeral: True
        if not voice_channel:
            await inter.response.send_message(
                embed=critical_error_embed(self.embed_color, admins_mentions),
                ephemeral=True
            )
            return

        # Ког MusicPlayer не загружен — ephemeral: True
        if not music_player:
            await inter.response.send_message(
                embed=invalid_input_embed(self.embed_color, owner=inter.author),
                ephemeral=True
            )
            return

        if действие == "Загнать":
            text_channel = inter.channel
            if isinstance(text_channel, disnake.TextChannel):
                try:
                    await text_channel.purge(limit=5, check=lambda m: not m.pinned)
                except Exception:
                    pass

            self.bot.loop.create_task(music_player.connect_and_play())

            embed = disnake.Embed(
                title="<:callcalling:1390972394268659753> Сержант подключился к сектору",
                description=(
                    f"> Голосовая связь **установлена** по приказу: {inter.author.mention}. "
                    f"Операция в полном разгаре, связь **стабильна** и под контролем штаба.\n\n"
                    f"<:channel:1390972349385281630> **Сектор:** {self.channel_mention(voice_channel)}\n"
                    f"<:calendar:1390972430780203058> **Время подключения:** {hours_time} по МСК"
                ),
                color=self.embed_color
            )
            embed.set_image(url="attachment://vocast.png")
            embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

            await inter.response.send_message(
                embed=embed,
                file=disnake.File(Speechify_Image, filename="vocast.png"),
                ephemeral=False
            )

        elif действие == "Выгнать":
            if not music_player.voice_client:
                # Бот не подключён ни к какому каналу — ephemeral: True
                await inter.response.send_message(
                    embed=critical_error_embed(self.embed_color, admins_mentions),
                    ephemeral=True
                )
                return

            try:
                await music_player.force_disconnect()
            except Exception:
                # Ошибка при отключении — ephemeral: True
                await inter.response.send_message(
                    embed=critical_error_embed(self.embed_color, admins_mentions),
                    ephemeral=True
                )
                return

            embed = disnake.Embed(
                title="<:callslash:1390972370508054578> Сержант покинул сектор",
                description=(
                    f"> Голосовая связь **разорвана** по приказу: {inter.author.mention}. "
                    f"Линия молчит, миссия окончена. **Ожидаем** новых распоряжений штаба.\n\n"
                    f"<:channel:1390972349385281630> **Сектор:** {self.channel_mention(voice_channel)}\n"
                    f"<:calendar:1390972430780203058> **Время отключения:** {hours_time} по МСК"
                ),
                color=self.embed_color
            )
            embed.set_image(url="attachment://vocast.png")
            embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

            await inter.response.send_message(
                embed=embed,
                file=disnake.File(Speechify_Image, filename="vocast.png"),
                ephemeral=False
            )