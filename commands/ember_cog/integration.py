import disnake
from disnake.ext import commands
from BANNED_FILES.config import Embed_Color, Video_Text, VIDEO_CHANNEL_ID, GROUP_MODER_ID

class IntegrationAnnouncer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.static_header = Video_Text

    @commands.slash_command(
        name="видео",
        description="Отправить интеграцию в youtube-дайджесты",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_messages=True)
    )
    async def video(
        self,
        ctx: disnake.ApplicationCommandInteraction,
        preview: str,
        title: str,
        youtube: str,
        vkontakte: str
    ):
        has_access = (
            any(role.id in GROUP_MODER_ID for role in ctx.author.roles)
            if isinstance(GROUP_MODER_ID, list)
            else any(role.id == GROUP_MODER_ID for role in ctx.author.roles)
        )

        if not has_access:
            embed = disnake.Embed(
                title="<:forbidden:1390972224436965386> Доступ к команде заблокирован",
                description=(
                    "У вас **отсутствуют полномочия** для выполнения данного приказа.\n\n"
                    ">>> Если вы считаете, что это ошибка — немедленно свяжитесь с адмиралом базы: "
                    f"{ctx.guild.owner.mention}"
                ),
                color=self.embed_color
            )

            await ctx.response.send_message(embed=embed, ephemeral=True)
            return

        channel = self.bot.get_channel(VIDEO_CHANNEL_ID)
        if not channel:
            await ctx.response.send_message(
                "❌ Канал не найден. Проверь VIDEO_CHANNEL_ID.", ephemeral=True
            )
            return

        embed = disnake.Embed(
            title=title,
            color=self.embed_color
        )
        embed.set_image(url=preview)
        embed.add_field(name="<:youtube:1390972086876377192> YouTube:", value=youtube, inline=False)
        embed.add_field(name="<:vk:1390972535298068570> ВКонтакте:", value=vkontakte, inline=False)
        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

        await channel.send(content=self.static_header, embed=embed)

        await ctx.response.send_message(
            f"📡 Интеграция успешно отправлена в {channel.mention}",
            ephemeral=True
        )
