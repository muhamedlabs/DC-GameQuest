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
            return

        # Получаем прошлый канал из Redis
        async with RedisManager() as redis:
            previous_record = await redis.load(SpeakerVoice, key="random_channel")

        previous_channel_id = (
            int(previous_record.random_channel_id)
            if previous_record and previous_record.random_channel_id
            else None
        )

        # Фильтруем список каналов
        available_channels = [
            vc for vc in category.voice_channels
            if vc.id != previous_channel_id
        ]

        if not available_channels:
            return

        selected_channel = random.choice(available_channels)

        record = SpeakerVoice(
            session_id="default",
            random_channel_id=str(selected_channel.id)
        )


        async with RedisManager() as redis:
            try:
                await redis.save(record, key="random_channel")
            except Exception:
                return

        # Проверяем, где сейчас бот
        voice_client = next(
            (v for v in self.bot.voice_clients if v.guild == guild),
            None
        )

        if voice_client and voice_client.is_connected():
            await asyncio.sleep(25)
            await voice_client.disconnect()

    async def get_current_channel(self) -> Optional[str]:
        async with RedisManager() as redis:
            try:
                record = await redis.load(SpeakerVoice, key="random_channel")
                return record.random_channel_id if record else None
            except Exception:
                return None

    async def delete_current_channel(self):
        async with RedisManager() as redis:
            try:
                await redis.delete(SpeakerVoice, key="random_channel")
            except Exception:
                return

    @daily_channel_change.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
