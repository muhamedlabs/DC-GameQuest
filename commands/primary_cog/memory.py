import disnake
import gc
import tracemalloc
import psutil
import logging
from disnake.ext import commands, tasks


class MemoryCleaner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        tracemalloc.start()
        self.clean_memory_loop.add_exception_type(Exception)
        self.clean_memory_loop.start()

    @tasks.loop(minutes=65)
    async def clean_memory_loop(self):
        try:
            process = psutil.Process()
            before_mem = process.memory_info().rss / 1024 / 1024  # В мегабайтах

            collected = gc.collect()

            after_mem = process.memory_info().rss / 1024 / 1024
            top_stats = tracemalloc.take_snapshot().statistics("lineno")

            logging.info(f"Очистка памяти вручную. Собрано объектов: {collected}")
            logging.info(f"Использование памяти: до {before_mem:.2f} MB → после {after_mem:.2f} MB")
            logging.info("Топ потребителей памяти:")
            for stat in top_stats[:5]:
                logging.info(stat)

        except Exception as e:
            logging.error(f"Ошибка в цикле очистки памяти: {e}")

    @clean_memory_loop.before_loop
    async def before_clean(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.clean_memory_loop.cancel()
