import disnake
from disnake.ext import commands
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import asyncio

from BANNED_FILES.config import RedisManager
from redis_storage.speaker_voice import SpeakerVoice

MSK = timezone(timedelta(hours=3))  # Московское время UTC+3


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} сек."
    elif seconds < 3600:
        minutes = seconds // 60
        sec = seconds % 60
        return f"{minutes} мин. {sec} сек."
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ч. {minutes} мин."
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days} дн. {hours} ч."


class VoiceSessionTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions: Dict[str, int] = {}  # channel_id -> session_id
        self.tasks = set()  # для хранения созданных задач
        self.bot.add_listener(self.on_voice_state_update)

    async def _get_next_session_id(self) -> int:
        key = ["voice_session_counter"]
        async with RedisManager() as redis:
            current = await redis.load(SpeakerVoice, key)
            if current is None:
                return 1
            return int(current.session_id) + 1

    async def _set_session_counter(self, value: int):
        key = ["voice_session_counter"]
        async with RedisManager() as redis:
            await redis.save(SpeakerVoice(session_id=value), key)

    async def record_voice_enter(self, channel_id: str) -> int:
        try:
            if channel_id in self.active_sessions:
                return self.active_sessions[channel_id]

            session_id = await self._get_next_session_id()

            session = SpeakerVoice(
                session_id=session_id,
                bot_id=str(self.bot.user.id),
                channel_id=channel_id,
                enter_voice_channel=datetime.now(MSK).isoformat()
            )

            key = [f"voice_session:{session_id}"]

            async with RedisManager() as redis:
                await redis.save(session, key, ttl=timedelta(days=3))
                await self._set_session_counter(session_id)

            self.active_sessions[channel_id] = session_id
            return session_id
        except Exception as e:
            print(f"[VoiceSessionTracker] record_voice_enter error: {e}")
            return 0

    async def record_voice_exit(self, channel_id: Optional[str] = None, session_id: Optional[int] = None):
        try:
            target_session_id = None

            if session_id:
                target_session_id = session_id
            elif channel_id and channel_id in self.active_sessions:
                target_session_id = self.active_sessions[channel_id]
            else:
                if len(self.active_sessions) == 1:
                    channel_id, target_session_id = next(iter(self.active_sessions.items()))
                else:
                    return

            if not target_session_id:
                return

            key = [f"voice_session:{target_session_id}"]
            async with RedisManager() as redis:
                session = await redis.load(SpeakerVoice, key)

                if not session or not session.enter_voice_channel:
                    if channel_id and channel_id in self.active_sessions:
                        del self.active_sessions[channel_id]
                    return

                if session.end_voice_channel:
                    if channel_id and channel_id in self.active_sessions:
                        del self.active_sessions[channel_id]
                    return

                start_time = datetime.fromisoformat(session.enter_voice_channel)
                end_time = datetime.now(MSK)
                duration = int((end_time - start_time).total_seconds())

                session.end_voice_channel = end_time.isoformat()
                session.time = format_duration(duration)

                await redis.save(session, key)

            if channel_id and channel_id in self.active_sessions:
                del self.active_sessions[channel_id]

        except Exception as e:
            print(f"[VoiceSessionTracker] record_voice_exit error: {e}")

    async def get_session_info(self, session_id: int) -> Optional[SpeakerVoice]:
        key = [f"voice_session:{session_id}"]
        async with RedisManager() as redis:
            return await redis.load(SpeakerVoice, key)

    async def cleanup_orphaned_sessions(self):
        try:
            current_voice_channels = set()
            for guild in self.bot.guilds:
                if guild.voice_client and guild.voice_client.channel:
                    current_voice_channels.add(str(guild.voice_client.channel.id))

            channels_to_remove = []
            for channel_id in self.active_sessions:
                if channel_id not in current_voice_channels:
                    channels_to_remove.append(channel_id)

            for channel_id in channels_to_remove:
                await self.record_voice_exit(channel_id=channel_id)
        except Exception as e:
            print(f"[VoiceSessionTracker] cleanup_orphaned_sessions error: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.id != self.bot.user.id:
            return

        async def handle():
            try:
                if not before.channel and after.channel:
                    await self.record_voice_enter(str(after.channel.id))
                elif before.channel and not after.channel:
                    await self.record_voice_exit(channel_id=str(before.channel.id))
                elif before.channel and after.channel and before.channel.id != after.channel.id:
                    await self.record_voice_exit(channel_id=str(before.channel.id))
                    await self.record_voice_enter(str(after.channel.id))
            except asyncio.CancelledError:
                raise
            except Exception:
                pass

        task = asyncio.create_task(handle())
        self.tasks.add(task)
        task.add_done_callback(lambda t: self.tasks.discard(t))

    async def cog_unload(self):
        # При выгрузке COG отменяем все задачи и ждём завершения
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

    async def cog_load(self):
        async def delayed_cleanup():
            try:
                await asyncio.sleep(5)
                await self.cleanup_orphaned_sessions()
            except Exception as e:
                print(f"[VoiceSessionTracker] delayed_cleanup error: {e}")

        self.bot.loop.create_task(delayed_cleanup())
