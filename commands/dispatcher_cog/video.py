import disnake
from disnake.ext import commands
from BANNED_FILES.config import Embed_Color, Video_Text, VIDEO_CHANNEL_ID, GROUP_MODER_IDS


class VideoIntegration(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.static_header: str = Video_Text

    @commands.slash_command(
        name="video",
        description="Отправить интеграцию в youtube-дайджесты",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_messages=True)
    )
    async def send_video_integration(
        self,
        inter: disnake.ApplicationCommandInteraction,
        preview_url: str = commands.Param(
            name="превью", description="Прямая ссылка на изображение превью (jpg или png)"
        ),
        title: str = commands.Param(
            name="название", description="Заголовок видеоматериала"
        ),
        youtube_link: str = commands.Param(
            name="ютуб", description="Ссылка на видео в YouTube"
        ),
        vk_link: str = commands.Param(
            name="вконтакте", description="Ссылка на видео во ВКонтакте", default=""
        )
    ):
        # Проверка наличия доступа
        has_access = (
            any(role.id in GROUP_MODER_IDS for role in inter.author.roles)
            if isinstance(GROUP_MODER_IDS, list)
            else any(role.id == GROUP_MODER_IDS for role in inter.author.roles)
        )

        if not has_access:
            embed = disnake.Embed(
                title="<:forbidden:1390972224436965386> Доступ к команде заблокирован",
                description=(
                    "У вас **отсутствуют полномочия** для выполнения данного приказа.\n\n"
                    ">>> Если вы считаете, что это ошибка — немедленно свяжитесь с адмиралом базы: "
                    f"{inter.guild.owner.mention}"
                ),
                color=self.embed_color
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        # Получение канала
        channel = self.bot.get_channel(VIDEO_CHANNEL_ID)
        if not channel:
            await inter.response.send_message(
                "Канал не найден. Проверь VIDEO_CHANNEL_ID.", ephemeral=True
            )
            return

        # Формирование Embed
        embed = disnake.Embed(
            title=title,
            color=self.embed_color
        )
        embed.set_image(url=preview_url)

        # Добавляем поля только если ссылки не пустые
        if youtube_link.strip():
            embed.add_field(name="<:youtube:1390972086876377192> YouTube:", value=youtube_link, inline=False)
        if vk_link.strip():
            embed.add_field(name="<:vk:1390972535298068570> VKontakte:", value=vk_link, inline=False)

        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

        # Отправка
        await channel.send(content=self.static_header, embed=embed)

        # Ответ
        await inter.response.send_message(
            f"Интеграция успешно отправлена в {channel.mention}",
            ephemeral=True
        )
