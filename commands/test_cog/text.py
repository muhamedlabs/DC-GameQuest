import disnake
from disnake.ext import commands
from disnake import Permissions
from disnake import InteractionContextTypes
from commands.information_cog.warnings import no_access_embed, system_error_embed, critical_error_embed, security_block_embed, invalid_input_embed
from BANNED_FILES.config import Embed_Color, GROUP_ADMIN_ID, ALLOWED_USER_IDS

class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(
        name="test",
        description="Отправляет заранее заданный текст"
    )

    @commands.contexts(bot_dm=False,  guild=True) # приватка и гільдія дозволи
    #@commands.default_member_permissions(moderate_members=True, administrator=True) # роли дозволи

    async def send_text(self, inter: disnake.AppCmdInter):

        owner = inter.guild.owner.mention if inter.guild and inter.guild.owner else "Нет владельца"
        admins_mentions = " ".join(f"<@{uid}>" for uid in ALLOWED_USER_IDS)

        has_access = (
            any(role.id in GROUP_ADMIN_ID for role in inter.author.roles)
            if isinstance(GROUP_ADMIN_ID, list)
            else any(role.id == GROUP_ADMIN_ID for role in inter.author.roles)
        )

        if not has_access:
            
            embed = no_access_embed(self.embed_color, owner, admins_mentions)

            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        await inter.response.send_message(
            "👋 Добро пожаловать на сервер Game Quest!\nСледите за новостями и оставайтесь с нами!",
            ephemeral=False
        )