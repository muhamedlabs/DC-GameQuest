import disnake
from disnake.ext import commands
import json
import os
from BANNED_FILES.config import Ban_Bot  # Путь к JSON-файлу со списком ID

# Загрузка чёрного списка
def load_ban_list():
    if os.path.exists(Ban_Bot):
        with open(Ban_Bot, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

# Сохранение чёрного списка
def save_ban_list(ban_list):
    with open(Ban_Bot, "w", encoding="utf-8") as f:
        json.dump(list(ban_list), f)

# Класс команды
class BotBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklist = load_ban_list()

    # Удаление сообщений от заблокированных (ботов и людей)
    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.id in self.blacklist:
            try:
                await message.delete()
                print(f"Сообщение от {message.author} ликвидировано. Десантник в чёрном списке.")
            except disnake.Forbidden:
                print("Нет прав на удаление сообщения.")
            except Exception as e:
                print(f"Ошибка удаления сообщения: {e}")

    # Блокировка команд у забаненных
    @commands.Cog.listener()
    async def on_application_command(self, inter: disnake.ApplicationCommandInteraction):
        if inter.author.id in self.blacklist:
            await inter.response.send_message(
                "🪖 Вы в чёрном списке штаба. Доступ к командам заблокирован.",
                ephemeral=True
            )
            raise commands.CheckFailure("Чёрный список штаба")

    # Slash-команда управления баном
    @commands.slash_command(
        name="ботбан",
        description="⚔️ Управление чёрным списком штаба (бан / разбан)",
        default_member_permissions=disnake.Permissions(administrator=True)
    )
    async def botban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(name="user", description="Укажи бойца для штабных санкций"),
        action: str = commands.Param(name="action", description="Выбери действие", choices=["забанить", "разбанить"])
    ):
        тип = "бот" if user.bot else "десантник"

        if action == "забанить":
            self.blacklist.add(user.id)
            save_ban_list(self.blacklist)
            await inter.response.send_message(
                f"{тип.capitalize()} {user.mention} добавлен в чёрный список штаба.",
                ephemeral=True
            )
        else:
            self.blacklist.discard(user.id)
            save_ban_list(self.blacklist)
            await inter.response.send_message(
                f"{тип.capitalize()} {user.mention} удалён из чёрного списка. Допуск восстановлен.",
                ephemeral=True
            )


