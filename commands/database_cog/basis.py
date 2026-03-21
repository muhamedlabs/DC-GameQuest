import disnake
from disnake.ext import commands

from BANNED_FILES.config import GROUP_ADMIN_ID

class UniversalCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Словарь доступных функций из других Cog'ов
        self.available_functions = {
            "data_users_notification": "Sync",
            "sync_data": "Sync",
            "backup_users": "Sync"
        }
    
    def check_permissions(self, inter):
        """Проверка разрешений пользователя"""
        return (
            any(role.id in GROUP_ADMIN_ID for role in inter.author.roles)
            if isinstance(GROUP_ADMIN_ID, list)
            else any(role.id == GROUP_ADMIN_ID for role in inter.author.roles)
        )
    
    @commands.slash_command(
        description="Универсальная команда для выполнения различных функций"
    )

    @commands.contexts(bot_dm=False,  guild=True)
    @commands.default_member_permissions(moderate_members=True, administrator=True)
    
    async def execute(
        self, 
        inter: disnake.ApplicationCommandInteraction,
        function_name: str = commands.Param(
            description="Название функции для выполнения",
            choices=[
                "data_users_notification",
                "sync_data", 
                "backup_users"
            ]
        )
    ):
        """Универсальная команда для выполнения различных функций"""
        
        # Проверка доступа
        if not self.check_permissions(inter):
            embed = disnake.Embed(
                title="<:forbidden:1390972224436965386> Доступ к команде заблокирован",
                description=(
                    "У вас **отсутствуют полномочия** для выполнения данного приказа.\n\n"
                    ">>> Если вы считаете, что это ошибка — немедленно свяжитесь с адмиралом базы: "
                    f"{inter.guild.owner.mention}"
                ),
                color=disnake.Color.red()
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Проверка существования функции
        if function_name not in self.available_functions:
            embed = disnake.Embed(
                title="❌ Функция не найдена",
                description=f"Функция `{function_name}` не существует или недоступна.",
                color=disnake.Color.red()
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Получение Cog'а и выполнение функции
        try:
            cog_name = self.available_functions[function_name]
            target_cog = self.bot.get_cog(cog_name)
            
            if not target_cog:
                embed = disnake.Embed(
                    title="❌ Cog не найден",
                    description=f"Cog `{cog_name}` не загружен или недоступен.",
                    color=disnake.Color.red()
                )
                await inter.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Получение функции из Cog'а
            target_function = getattr(target_cog, function_name, None)
            
            if not target_function:
                embed = disnake.Embed(
                    title="❌ Функция не найдена в Cog",
                    description=f"Функция `{function_name}` не найдена в Cog `{cog_name}`.",
                    color=disnake.Color.red()
                )
                await inter.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Выполнение функции
            await target_function(inter)
            
        except Exception as e:
            embed = disnake.Embed(
                title="❌ Ошибка выполнения",
                description=f"Произошла ошибка при выполнении функции: ```{str(e)}```",
                color=disnake.Color.red()
            )
            if not inter.response.is_done():
                await inter.response.send_message(embed=embed, ephemeral=True)
            else:
                await inter.edit_original_response(embed=embed)


def setup(bot):
    bot.add_cog(UniversalCommands(bot))