import disnake
from disnake.ext import commands, tasks

class StatusBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.status_list = [
            "YouTube: Game Quest",
            "Telegram: Game Quest", 
            "muhamedlabs.pro"
        ]
        self.current_status = 0
        self.status_task.start()

    @tasks.loop(minutes=15)
    async def status_task(self):
        status_name = self.status_list[self.current_status]

        await self.bot.change_presence(
            status=disnake.Status.idle,
            activity=disnake.Activity(
                type=disnake.ActivityType.watching,
                name=status_name
            )
        )

        self.current_status = (self.current_status + 1) % len(self.status_list)

    @status_task.before_loop
    async def before_status_task(self):
        await self.bot.wait_until_ready()
