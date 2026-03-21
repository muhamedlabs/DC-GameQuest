import disnake
from disnake.ext import commands
from datetime import datetime, timezone, timedelta

from BANNED_FILES.config import Embed_Color, Video_Text, VIDEO_CHANNEL_ID, GROUP_MODER_IDS, RedisManager
from redis_storage.dispatcher_message import DispatcherMessage

MSK = timezone(timedelta(hours=3))  # Московское время UTC+3
message_lifetime = timedelta(hours=48)

class VideoIntegration(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.static_header: str = Video_Text

    @commands.slash_command(
        name="video",
        description="Отправить интеграцию в youtube-дайджесты"
    )

    @commands.contexts(bot_dm=False,  guild=True)
    @commands.default_member_permissions(manage_messages=True, moderate_members=True, administrator=True)

    async def send_video_integration(
        self,
        inter: disnake.ApplicationCommandInteraction,
        preview_url: str = commands.Param(
            name="превью",
            description="Прямая ссылка на изображение превью (jpg или png)"
        ),
        title: str = commands.Param(
            name="название",
            description="Заголовок видеоматериала"
        ),
        youtube_link: str = commands.Param(
            name="ютуб",
            description="Ссылка на видео в YouTube"
        ),
        vk_link: str = commands.Param(
            name="вконтакте",
            description="Ссылка на видео во ВКонтакте",
            default=""
        )
    ):
        await inter.response.defer(ephemeral=True)

        has_access = (
            any(role.id in GROUP_MODER_IDS for role in inter.author.roles)
            if isinstance(GROUP_MODER_IDS, list)
            else any(role.id == GROUP_MODER_IDS for role in inter.author.roles)
        )

        if not has_access:
            await inter.edit_original_response(
                embed=disnake.Embed(
                    title="<:forbidden:1390972224436965386> Доступ запрещён",
                    description="У вас нет прав на выполнение данной команды.",
                    color=self.embed_color
                )
            )
            return

        channel = self.bot.get_channel(VIDEO_CHANNEL_ID)
        if not channel:
            await inter.edit_original_response(
                "Канал не найден. Проверь VIDEO_CHANNEL_ID."
            )
            return

        embed = disnake.Embed(
            title=title,
            color=self.embed_color
        )
        embed.set_image(url=preview_url)

        if youtube_link.strip():
            embed.add_field(
                name="<:youtube:1390972086876377192> YouTube:",
                value=youtube_link,
                inline=False
            )

        if vk_link.strip():
            embed.add_field(
                name="<:vk:1390972535298068570> VKontakte:",
                value=vk_link,
                inline=False
            )

        embed.set_footer(
            text="Благодарим за проявленный интерес к нашему спецпроекту!"
        )

        message: disnake.Message = await channel.send(
            content=self.static_header,
            embed=embed
        )

        record = DispatcherMessage(
            id=str(message.id)[:8],
            message_id=str(message.id),
            channel_id=str(channel.id),
            user_id=str(inter.author.id),
            username=inter.author.name,
            timestamp=datetime.now(MSK).strftime("%d.%m.%Y %H:%M:%S")
        )

        async with RedisManager() as redis:
            await redis.save(
                record,
                key=f"video:{record.id}",
                ttl=message_lifetime
            )

        await inter.edit_original_response(
            f"Интеграция успешно отправлена в {channel.mention}"
        )
