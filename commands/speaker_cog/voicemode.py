import disnake
from disnake.ext import commands

from BANNED_FILES.config import Embed_Color, GROUP_ADMIN_ID, ALLOWED_USER_IDS, Speechify_Image

from commands.information_cog.warnings import critical_error_embed, invalid_input_embed, no_access_embed

from commands.information_cog.time import hours_time


class VoiceControl(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    def get_current_voice_channel(
        self,
    ) -> disnake.VoiceChannel | None:

        music_player = self.bot.get_cog("MusicPlayer")

        if music_player is None:
            return None

        if music_player.is_disconnected():
            return None

        voice_client = music_player.voice_client

        if voice_client is None:
            return None

        channel = voice_client.channel

        if not isinstance(channel, disnake.VoiceChannel):
            return None

        return channel

    def channel_mention(
        self,
        channel: disnake.abc.GuildChannel | None,
    ) -> str:
        if channel is None:
            return "—"

        return f"<#{channel.id}>"

    @commands.slash_command(name="bot_voice",description="Управление голосовой связью с сержантом")
    
    @commands.contexts(bot_dm=False,guild=True,)
    @commands.default_member_permissions(manage_messages=True, moderate_members=True, administrator=True)

    async def voice(
        self,
        inter: disnake.ApplicationCommandInteraction,
        действие: str = commands.Param(
            choices=["Загнать", "Выгнать"],
            description="Приказ для сержанта",
        ),
    ):
        admins_mentions = " ".join(
            f"<@{uid}>"
            for uid in ALLOWED_USER_IDS
        )

        if isinstance(GROUP_ADMIN_ID, list):
            has_access = any(
                role.id in GROUP_ADMIN_ID
                for role in inter.author.roles
            )
        else:
            has_access = any(
                role.id == GROUP_ADMIN_ID
                for role in inter.author.roles
            )

        if not has_access:
            await inter.response.send_message(
                embed=no_access_embed(
                    self.embed_color,
                    owner=inter.author,
                ),
                ephemeral=True,
            )
            return

        music_player = self.bot.get_cog("MusicPlayer")

        if music_player is None:
            await inter.response.send_message(
                embed=invalid_input_embed(
                    self.embed_color,
                    owner=inter.author,
                ),
                ephemeral=True,
            )
            return

        if действие == "Загнать":

            voice_channel = (
                await music_player.get_voice_channel()
            )

            if voice_channel is None:
                await inter.response.send_message(
                    embed=critical_error_embed(
                        self.embed_color,
                        admins_mentions,
                    ),
                    ephemeral=True,
                )
                return

            # Очищаем последние сообщения в текстовом канале
            text_channel = inter.channel

            if isinstance(
                text_channel,
                disnake.TextChannel,
            ):
                try:
                    await text_channel.purge(
                        limit=5,
                        check=lambda m: not m.pinned,
                    )
                except Exception:
                    pass

            # Запускаем MusicPlayer
            self.bot.loop.create_task(
                music_player.connect_and_play()
            )

            embed = disnake.Embed(
                title=(
                    "<:callcalling:1390972394268659753> Сержант подключился к сектору"
                ),
                description=(
                    f"> Голосовая связь **установлена** по приказу: {inter.author.mention}. Операция в полном разгаре, связь "
                    f"**стабильна** и под контролем штаба.\n\n"

                    f"<:channel:1390972349385281630> **Сектор:** {self.channel_mention(voice_channel)}\n"

                    f"<:calendar:1390972430780203058> **Время подключения:** {hours_time} по МСК"
                ),
                color=self.embed_color,
            )

            embed.set_image(
                url="attachment://vocast.png"
            )

            embed.set_footer(
                text=(
                    "Благодарим за проявленный интерес к нашему спецпроекту!"
                )
            )

            await inter.response.send_message(
                embed=embed,
                file=disnake.File(
                    Speechify_Image,
                    filename="vocast.png",
                ),
                ephemeral=False,
            )

            return

        if действие == "Выгнать":

            current_channel = (
                self.get_current_voice_channel()
            )

            if current_channel is None:
                await inter.response.send_message(
                    embed=critical_error_embed(
                        self.embed_color,
                        admins_mentions,
                    ),
                    ephemeral=True,
                )
                return

            current_channel_mention = (
                self.channel_mention(current_channel)
            )

            try:
                await music_player.force_disconnect()

            except Exception:
                await inter.response.send_message(
                    embed=critical_error_embed(
                        self.embed_color,
                        admins_mentions,
                    ),
                    ephemeral=True,
                )
                return

            embed = disnake.Embed(
                title=(
                    "<:callslash:1392378054578> Сержант покинул сектор"
                ),
                description=(
                    f"> Голосовая связь **разорвана** по приказу: {inter.author.mention}. Линия молчит, миссия окончена. "
                    f"**Ожидаем** новых распоряжений штаба.\n\n"

                    f"<:channel:1390972349385281630> **Сектор:** {current_channel_mention}\n"

                    f"<:calendar:1390972430780203058> **Время отключения:** {hours_time} по МСК"
                ),
                color=self.embed_color,
            )

            embed.set_image(
                url="attachment://vocast.png"
            )

            embed.set_footer(
                text=(
                    "Благодарим за проявленный интерес к нашему спецпроекту!"
                )
            )

            await inter.response.send_message(
                embed=embed,
                file=disnake.File(
                    Speechify_Image,
                    filename="vocast.png",
                ),
                ephemeral=False,
            )
