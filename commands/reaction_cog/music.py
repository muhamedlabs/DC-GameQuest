import disnake
from disnake.ext import commands
import asyncio

from BANNED_FILES.config import Musical_Reaction


class ReactionMusic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.emoji_ids = Musical_Reaction
        self.pending_tasks: set[asyncio.Task] = set()  # отслеживаем все таски

    def cog_unload(self):
        """Отменяем все активные таски при выгрузке COG"""
        for task in self.pending_tasks:
            task.cancel()
        self.pending_tasks.clear()

    def get_target_channel_id(self) -> int | None:
        music_player = self.bot.get_cog("MusicPlayer")

        if music_player is None or music_player.is_disconnected():
            return None

        return music_player.voice_client.channel.id

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
            target_channel_id = self.get_target_channel_id()
            if not target_channel_id or message.channel.id != target_channel_id:
                return
            await self.add_reactions_later(message)
        except asyncio.CancelledError:
            return
        except Exception:
            return