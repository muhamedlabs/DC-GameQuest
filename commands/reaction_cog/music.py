import disnake
from disnake.ext import commands
import asyncio

from BANNED_FILES.config import Musical_Reaction, RedisManager
from redis_storage.speaker_voice import SpeakerVoice


class ReactionMusic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.emoji_ids = Musical_Reaction
        self.redis = RedisManager()
        self.pending_tasks: set[asyncio.Task] = set()  # отслеживаем все таски

    def cog_unload(self):
        """Отменяем все активные таски при выгрузке COG"""
        for task in self.pending_tasks:
            task.cancel()
        self.pending_tasks.clear()

    async def get_target_channel_id(self) -> int | None:
        try:
            async with self.redis as redis:
                record = await redis.load(SpeakerVoice, key="random_channel")
                if not record or not record.random_channel_id:
                    return None
                return int(record.random_channel_id)
        except Exception:
            return None

    async def add_reactions_later(self, message: disnake.Message):
        try:
            await asyncio.sleep(25)
            for emoji_id in self.emoji_ids:
                emoji = self.bot.get_emoji(emoji_id)
                if emoji:
                    try:
                        await message.add_reaction(emoji)
                    except Exception:
                        pass
        except asyncio.CancelledError:
            # Если таск отменён при выгрузке — выходим без ошибок
            return
        except Exception:
            return

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        task = asyncio.create_task(self.safe_add_reactions(message))
        self.pending_tasks.add(task)
        task.add_done_callback(lambda t: self.pending_tasks.discard(task))

    async def safe_add_reactions(self, message: disnake.Message):
        try:
            target_channel_id = await self.get_target_channel_id()
            if not target_channel_id or message.channel.id != target_channel_id:
                return
            await self.add_reactions_later(message)
        except asyncio.CancelledError:
            return
        except Exception:
            return

