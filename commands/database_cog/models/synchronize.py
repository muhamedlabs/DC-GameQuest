import disnake
from disnake.ext import commands
import json

from BANNED_FILES.config import RedisManager, Embed_Color, Users_Notification, GROUP_ADMIN_ID
from commands.database_cog.users_notification import UsersNotification

class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(
        description="Загрузка UsersNotification.json",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_messages=True)
    )
    async def data_users_notification(self, inter: disnake.ApplicationCommandInteraction):
        # Проверка на доступ до выполнения
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

        await inter.response.defer(ephemeral=True)

        async with RedisManager() as redis:
            data = await redis.load_many(record_type=UsersNotification, key="*")
            data = [i.to_dict() for i in data]

        with open(Users_Notification, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        await inter.edit_original_response(content="Загрузка завершена! Файл UsersNotification.json")
