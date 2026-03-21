import disnake
from disnake.ext import commands
from disnake import Permissions
from disnake import InteractionContextTypes
from BANNED_FILES.config import Embed_Color, GROUP_ADMIN_ID

class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(
        name="test",
        description="Отправляет заранее заданный текст"
    )

    @commands.contexts(bot_dm=False,  guild=True)
    @commands.default_member_permissions(moderate_members=True, administrator=True)

    async def send_text(self, inter: disnake.AppCmdInter):

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
                    f">>> Если это ошибка — свяжитесь с администратором: {inter.guild.owner.mention}"
                ),
                color=self.embed_color
            )

            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        await inter.response.send_message(
            "👋 Добро пожаловать на сервер Game Quest!\nСледите за новостями и оставайтесь с нами!",
            ephemeral=True
        )