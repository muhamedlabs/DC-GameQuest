import disnake
from disnake.ext import commands, tasks
from BANNED_FILES.config import Activity_Bot

class StatusBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.status_list = Activity_Bot
        self.current_status = 0
        self.status_task.start()

    @tasks.loop(minutes=15)
    async def status_task(self):
        """Автоматически меняет статус бота каждые 15 минут"""
        status_name = self.status_list[self.current_status]

        # Устанавливаем статус "Не активен" (idle)
        await self.bot.change_presence(
            status=disnake.Status.idle,
            activity=disnake.Activity(
                type=disnake.ActivityType.watching,
                name=status_name
            )
        )

        # Переход к следующему статусу
        self.current_status = (self.current_status + 1) % len(self.status_list)

    @status_task.before_loop
    async def before_status_task(self):
        """Ожидаем полной загрузки бота перед запуском задачи"""
        await self.bot.wait_until_ready()