import re
import disnake
from disnake.ext import commands
from datetime import datetime, timezone, timedelta

from BANNED_FILES.config import Embed_Color, Video_Text, VIDEO_CHANNEL_ID, GROUP_MODER_IDS, RedisManager
from commands.information_cog.warnings import security_block_embed
from commands.information_cog.time import hours_time
from redis_storage.dispatcher_message import DispatcherMessage

message_lifetime = timedelta(hours=48)

IMAGE_URL_PATTERN = re.compile(r"^https?://\S+\.(jpg|jpeg|png|gif|webp)(\?\S*)?$", re.IGNORECASE)


def is_valid_image_url(url: str) -> bool:
    return bool(url and IMAGE_URL_PATTERN.match(url.strip()))


class VideoIntegration(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.static_header: str = Video_Text

    def _has_access(self, inter: disnake.ApplicationCommandInteraction) -> bool:
        if isinstance(GROUP_MODER_IDS, list):
            return any(role.id in GROUP_MODER_IDS for role in inter.author.roles)
        return any(role.id == GROUP_MODER_IDS for role in inter.author.roles)

    def _build_embed(self, title: str, preview_url: str, youtube_link: str, vk_link: str) -> disnake.Embed:
        embed = disnake.Embed(title=title, color=self.embed_color)

        if preview_url:
            embed.set_image(url=preview_url)

        if youtube_link and youtube_link.strip():
            embed.add_field(
                name="<:youtube:1390972086876377192> YouTube:",
                value=youtube_link,
                inline=False
            )

        if vk_link and vk_link.strip():
            embed.add_field(
                name="<:vk:1390972535298068570> VKontakte:",
                value=vk_link,
                inline=False
            )

        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
        return embed

    @commands.slash_command(
        name="video",
        description="Отправить видео-интеграцию (укажи ID, чтобы отредактировать)"
    )
    @commands.contexts(bot_dm=False, guild=True)
    #@commands.default_member_permissions(manage_messages=True, moderate_members=True, administrator=True)
    async def send_video_integration(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str = commands.Param(
            name="название",
            description="Заголовок видеоматериала"
        ),
        preview_url: str = commands.Param(
            name="превью",
            description="Прямая ссылка на превью (jpg/png/gif/webp)"
        ),
        youtube_link: str = commands.Param(
            name="ютуб",
            description="Ссылка на видео в YouTube"
        ),
        vk_link: str = commands.Param(
            name="вконтакте",
            description="Ссылка на видео во ВКонтакте",
            default=""
        ),
        record_id: str = commands.Param(
            name="id",
            description="ID записи для редактирования (первые 8 символов)",
            default=None
        )
    ):
        await inter.response.defer(ephemeral=True)

        owner = inter.guild.owner.mention if inter.guild and inter.guild.owner else "Не назначен"

        if not self._has_access(inter):
            await inter.edit_original_response(embed=security_block_embed(self.embed_color, owner))
            return

        # ── Режим редактирования ────────────────────────────────────────────
        if record_id:
            async with RedisManager() as redis:
                record = await redis.load(DispatcherMessage, key=f"video:{record_id}")

            if not record:
                await inter.edit_original_response(
                    "Запись с таким ID не найдена или истёк срок хранения (48 часов)."
                )
                return

            channel = self.bot.get_channel(int(record.channel_id))
            if not channel:
                await inter.edit_original_response("Канал не найден.")
                return

            try:
                message = await channel.fetch_message(int(record.message_id))
            except disnake.NotFound:
                await inter.edit_original_response("Исходное сообщение не найдено — возможно, было удалено.")
                return

            if preview_url and not is_valid_image_url(preview_url):
                await inter.edit_original_response(
                    "Ссылка на превью некорректна. Нужна прямая ссылка на .jpg/.png/.gif/.webp"
                )
                return

            old_embed = message.embeds[0] if message.embeds else disnake.Embed(color=self.embed_color)

            old_youtube = old_vk = None
            for field in old_embed.fields:
                if "YouTube" in field.name:
                    old_youtube = field.value
                elif "VKontakte" in field.name:
                    old_vk = field.value

            new_embed = self._build_embed(
                title=title or old_embed.title,
                preview_url=preview_url or (old_embed.image.url if old_embed.image else None),
                youtube_link=youtube_link or old_youtube,
                vk_link=vk_link or old_vk,
            )

            await message.edit(embed=new_embed)
            await inter.edit_original_response(f"Сообщение в {channel.mention} обновлено.")
            return

        # ── Режим создания нового сообщения ─────────────────────────────────
        if not is_valid_image_url(preview_url):
            await inter.edit_original_response(
                "Ссылка на превью некорректна. Нужна прямая ссылка на .jpg/.png/.gif/.webp"
            )
            return

        channel = self.bot.get_channel(VIDEO_CHANNEL_ID)
        if not channel:
            await inter.edit_original_response("Канал не найден. Проверь VIDEO_CHANNEL_ID.")
            return

        embed = self._build_embed(title, preview_url, youtube_link, vk_link)

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
            timestamp=hours_time
        )

        async with RedisManager() as redis:
            await redis.save(
                record,
                key=f"video:{record.id}",
                ttl=message_lifetime
            )

        await inter.edit_original_response(
            f"Интеграция успешно отправлена в {channel.mention}\nID для редактирования: `{record.id}`"
        )