import disnake
from disnake.ext import commands
import asyncio

class DeleteMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        # Игнорируем сообщения от бота
        if message.author.bot:
            return

        # Проверяем, что сообщение начинается с "!"
        if message.content.startswith('!'):
            # Запускаем фоновую задачу удаления
            asyncio.create_task(self._delayed_delete(message))

    async def _delayed_delete(self, message: disnake.Message):
        try:
            await asyncio.sleep(10)  # Ждём 10 секунд
            await message.delete()
        except disnake.NotFound:
            # Сообщение уже удалено, ничего делать не нужно
            pass
        except disnake.Forbidden:
            # Нет прав на удаление сообщения
            pass
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")
