import disnake
from disnake.ext import commands
from datetime import timedelta
from urllib.parse import urlparse

from BANNED_FILES.config import Embed_Color, Video_Text, Community_Image, VIDEO_CHANNEL_ID, GROUP_MODER_IDS, ALLOWED_USER_IDS, RedisManager
from commands.information_cog.warnings import security_block_embed, invalid_input_embed, record_not_found_embed
from commands.information_cog.time import hours_time
from redis_storage.dispatcher_message import DispatcherMessage
from redis_storage.auto_messages import AutoMessages

message_lifetime = timedelta(days=90)
confirmation_lifetime = timedelta(hours=1)


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".gif", ".webp")
YOUTUBE_DOMAINS = ("youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com")
VK_DOMAINS = ("vk.com", "www.vk.com", "m.vk.com")


def _parsed_url(url: str):
    if not url or not url.strip():
        return None
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return parsed


def is_valid_image_url(url: str) -> bool:
    parsed = _parsed_url(url)
    return bool(parsed and parsed.path.lower().endswith(IMAGE_EXTENSIONS))


def is_valid_youtube_url(url: str) -> bool:
    parsed = _parsed_url(url)
    return bool(parsed and parsed.netloc.lower() in YOUTUBE_DOMAINS)


def is_valid_vk_url(url: str) -> bool:
    parsed = _parsed_url(url)
    return bool(parsed and parsed.netloc.lower() in VK_DOMAINS)


class VideoIntegration(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.static_header: str = Video_Text

    def _has_access(self, inter: disnake.ApplicationCommandInteraction) -> bool:
        if isinstance(GROUP_MODER_IDS, list):
            return any(role.id in GROUP_MODER_IDS for role in inter.author.roles)
        return any(role.id == GROUP_MODER_IDS for role in inter.author.roles)

    def _build_embed(
        self,
        title: str,
        preview_url: str,
        youtube_link: str,
        vk_link: str,
    ) -> disnake.ui.Container:
        components = []

        components.append(
            disnake.ui.TextDisplay(
                content=f"## <:videooctagon:1525766965292040252> {title}"
            )
        )
        components.append(disnake.ui.Separator())

        if self.static_header:
            components.append(disnake.ui.TextDisplay(content=self.static_header))

        if youtube_link and youtube_link.strip():
            components.append(
                disnake.ui.TextDisplay(
                    content=(
                        "### <:youtube:1390972086876377192> YouTube:\n"
                        f"{youtube_link}"
                    )
                )
            )

        if vk_link and vk_link.strip():
            components.append(
                disnake.ui.TextDisplay(
                    content=(
                        "### <:vk:1390972535298068570> VKontakte:\n"
                        f"{vk_link}"
                    )
                )
            )

        if preview_url:
            components.append(
                disnake.ui.MediaGallery(
                    disnake.MediaGalleryItem(media=preview_url)
                )
            )

        components.append(disnake.ui.Separator())
        components.append(
            disnake.ui.TextDisplay(
                content="-# Благодарим за проявленный интерес к нашему спецпроекту!"
            )
        )

        return disnake.ui.Container(
            *components,
            accent_colour=self.embed_color,
        )

    def _confirmation_embed(
        self,
        channel: disnake.TextChannel,
        record_id: str,
        author: disnake.Member,
        edited: bool = False,
    ) -> tuple[disnake.Embed, disnake.File]:
        action = "обновлена" if edited else "отправлена"
        embed = disnake.Embed(
            title="<:videooctagon:1525766965292040252> Интеграция с видео успешно " + action,
            description=(
                f"> Оперативная **видеозапись** успешно зарегистрирована. Архивирование завершено, материал **готов** к дальнейшему **использованию**.\n\n"
                f"Материал размещён в канале: {channel.mention}\n"
                f"Отправил лейтенант: {author.mention}\n\n"
                f"ID для редактирования: ```{record_id}```\n\n"
                f"Срок хранения данного сообщения ограничен. Автоматическое удаление будет выполнено через 24 часа."
            ),
            color=self.embed_color,
        )
        file = disnake.File(Community_Image, filename="community.png")
        embed.set_image(url="attachment://community.png")
        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
        return embed, file

    async def _send_confirmation(
        self,
        inter: disnake.ApplicationCommandInteraction,
        record_id: str,
        channel: disnake.TextChannel,
        author: disnake.Member,
        edited: bool,
    ):
        """Отправляет подтверждение и удаляет предыдущее сообщение, если оно существует"""
        key = f"video_confirm:{record_id}"

        async with RedisManager() as redis:
            previous = await redis.load(AutoMessages, key=key)

            if previous and previous.message_id is not None and previous.channel_id is not None:
                try:
                    old_channel = self.bot.get_channel(int(previous.channel_id))
                    if old_channel:
                        old_message = await old_channel.fetch_message(int(previous.message_id))
                        await old_message.delete()
                except (disnake.NotFound, disnake.Forbidden):
                    pass

            confirm_embed, confirm_file = self._confirmation_embed(channel, record_id, author, edited=edited)
            new_message = await inter.channel.send(
                embed=confirm_embed,
                file=confirm_file,
                delete_after=confirmation_lifetime.total_seconds(),
            )

            auto_record = AutoMessages(
                id=record_id,
                message_id=str(new_message.id),
                channel_id=str(inter.channel.id),
                timestamp=hours_time,
            )
            await redis.save(auto_record, key=key, ttl=confirmation_lifetime)

    @commands.slash_command(
        name="video",
        description="Отправить видео-интеграцию в канал",
    )
    @commands.contexts(bot_dm=False, guild=True)
    @commands.default_member_permissions(manage_messages=True, moderate_members=True, administrator=True)
    async def send_video_integration(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str = commands.Param(name="название", description="Наименование видеоматериалов операции"),
        preview_url: str = commands.Param(name="превью", description="Прямая ссылка на превью или изображение"),
        youtube_link: str = commands.Param(name="ютуб", description="Ссылка на видео в YouTube"),
        vk_link: str = commands.Param(name="вконтакте", description="Ссылка на видео во ВКонтакте", default=""),
        record_id: str = commands.Param(name="id", description="ID записи для редактирования", default=None),
    ):
        owner = inter.guild.owner.mention if inter.guild and inter.guild.owner else "Не назначен"
        admins_mentions = " ".join(f"<@{uid}>" for uid in ALLOWED_USER_IDS)

        await inter.response.defer(ephemeral=True)

        if not self._has_access(inter):
            await inter.edit_original_response(
                embed=security_block_embed(self.embed_color, owner)
            )
            return

        # Режим редактирования
        if record_id:
            async with RedisManager() as redis:
                record = await redis.load(DispatcherMessage, key=f"video_embed:{record_id}")

            if not record:
                await inter.edit_original_response(embed=record_not_found_embed(self.embed_color, owner))
                return

            channel = self.bot.get_channel(int(record.channel_id))
            if not channel:
                await inter.edit_original_response(embed=record_not_found_embed(self.embed_color, owner))
                return

            try:
                message = await channel.fetch_message(int(record.message_id))
            except disnake.NotFound:
                await inter.edit_original_response(embed=record_not_found_embed(self.embed_color, owner))
                return

            if preview_url and not is_valid_image_url(preview_url):
                await inter.edit_original_response(embed=invalid_input_embed(self.embed_color, admins_mentions))
                return

            if youtube_link and not is_valid_youtube_url(youtube_link):
                await inter.edit_original_response(embed=invalid_input_embed(self.embed_color, admins_mentions))
                return

            if vk_link and vk_link.strip() and not is_valid_vk_url(vk_link):
                await inter.edit_original_response(embed=invalid_input_embed(self.embed_color, admins_mentions))
                return

            new_container = self._build_embed(
                title=title,
                preview_url=preview_url,
                youtube_link=youtube_link,
                vk_link=vk_link,
            )

            await message.edit(
                content=None,
                embed=None,
                components=[new_container],
            )

            await inter.delete_original_response()
            await self._send_confirmation(inter, record.id, channel, inter.author, edited=True)
            return

        # Режим создания — проверки синхронные
        if not is_valid_image_url(preview_url):
            await inter.edit_original_response(
                embed=invalid_input_embed(self.embed_color, admins_mentions)
            )
            return

        if not is_valid_youtube_url(youtube_link):
            await inter.edit_original_response(
                embed=invalid_input_embed(self.embed_color, admins_mentions)
            )
            return

        if vk_link and vk_link.strip() and not is_valid_vk_url(vk_link):
            await inter.edit_original_response(
                embed=invalid_input_embed(self.embed_color, admins_mentions)
            )
            return

        channel = self.bot.get_channel(VIDEO_CHANNEL_ID)
        if not channel:
            await inter.edit_original_response(
                embed=invalid_input_embed(self.embed_color, admins_mentions)
            )
            return

        container = self._build_embed(title, preview_url, youtube_link, vk_link)
        message: disnake.Message = await channel.send(components=[container])

        record = DispatcherMessage(
            id=str(message.id)[:8],
            message_id=str(message.id),
            channel_id=str(channel.id),
            user_id=str(inter.author.id),
            username=inter.author.name,
            timestamp=hours_time,
        )

        async with RedisManager() as redis:
            await redis.save(record, key=f"video:{record.id}", ttl=message_lifetime)

        await inter.delete_original_response()
        await self._send_confirmation(inter, record.id, channel, inter.author, edited=False)
