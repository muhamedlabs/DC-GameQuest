import random
from typing import Optional
from disnake.ext import tasks, commands
from BANNED_FILES.config import SPEAKER_CATEGORY_ID, RedisManager
from redis_storage.speaker_voice import SpeakerVoice
import asyncio

class RoomSelector(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_channel_change.start()

    @tasks.loop(hours=24)
    async def daily_channel_change(self):
        guild = self.bot.guilds[0]
        category = guild.get_channel(SPEAKER_CATEGORY_ID)
        if not category or not category.voice_channels:
            print("[RoomSelector] В категории нет голосовых каналов")
            return

        # Выбираем новый случайный канал и сохраняем в Redis
        selected_channel = random.choice(category.voice_channels)
        record = SpeakerVoice(session_id="default", random_channel_id=str(selected_channel.id))

        async with RedisManager() as redis:
            try:
                await redis.save(record, key="random_channel")
            except Exception as e:
                print(f"[RoomSelector] Ошибка сохранения в Redis: {e}")

        # Проверяем, где сейчас бот
        voice_client = None
        for vc in guild.voice_channels:
            if self.bot.user in vc.members:
                # Находим голосовой клиент бота
                voice_client = next((v for v in self.bot.voice_clients if v.guild == guild), None)
                break

        # Если бот в голосовом канале — ждем 25 секунд перед отключением
        if voice_client and voice_client.is_connected():
            print(f"[RoomSelector] Бот сейчас в канале {voice_client.channel.name}, отключаем через 25 секунд...")
            await asyncio.sleep(25)
            await voice_client.disconnect()
            print(f"[RoomSelector] Бот отключен от канала {voice_client.channel.name}")

    async def get_current_channel(self) -> Optional[str]:
        async with RedisManager() as redis:
            try:
                record = await redis.load(SpeakerVoice, key="random_channel")
                return record.random_channel_id if record else None
            except Exception as e:
                print(f"[RoomSelector] Ошибка получения из Redis: {e}")
                return None

    async def delete_current_channel(self):
        async with RedisManager() as redis:
            try:
                await redis.delete(SpeakerVoice, key="random_channel")
            except Exception as e:
                print(f"[RoomSelector] Ошибка удаления из Redis: {e}")

    @daily_channel_change.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
