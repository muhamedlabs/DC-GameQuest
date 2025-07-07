import disnake
from disnake.ext import commands
from BANNED_FILES.config import Embed_Color, GROUP_ADMIN_ID

class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(
        name="текст",
        description="Отправляет заранее заданный текст.",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_messages=True)
    )
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
                    ">>> Если вы считаете, что это ошибка — немедленно свяжитесь с адмиралом базы: "
                    f"{inter.guild.owner.mention}"
                ),
                color=self.embed_color
            )

            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        await inter.response.send_message(
            "👋 Добро пожаловать на сервер Game Quest!\nСледите за новостями и оставайтесь с нами!",
            ephemeral=True
        )
