import random
from typing import Optional
from disnake.ext import tasks, commands
from BANNED_FILES.config import SPEAKER_CATEGORY_ID, RedisManager
from redis_storage.speaker_voice import SpeakerVoice

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

        selected_channel = random.choice(category.voice_channels)
        record = SpeakerVoice(session_id="default", random_channel_id=str(selected_channel.id))

        async with RedisManager() as redis:
            try:
                await redis.save(record, key="random_channel")
            except Exception as e:
                print(f"[RoomSelector] Ошибка сохранения в Redis: {e}")

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
