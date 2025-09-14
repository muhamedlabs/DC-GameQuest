import os
import random
import asyncio
import subprocess
import disnake
import logging
from disnake.ext import commands, tasks
from BANNED_FILES.config import Music_Folder, Volume_Music, RedisManager
from redis_storage.speaker_voice import SpeakerVoice

logging.getLogger("disnake.voice_client").setLevel(logging.CRITICAL)

class MusicPlayer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_client: disnake.VoiceClient | None = None
        self.music_folder = Music_Folder
        self.volume = Volume_Music
        self.integration_cog = None
        self.last_disconnect_time: float | None = None
        self.connecting_lock = asyncio.Lock()
        self.auto_reconnect.start()

    def is_disconnected(self) -> bool:
        return (
            self.voice_client is None
            or not self.voice_client.is_connected()
            or self.voice_client.channel is None
        )

    async def force_disconnect(self):
        if self.voice_client:
            try:
                await self.voice_client.disconnect(force=True)
                self.voice_client.cleanup()
            except Exception as e:
                print(f"[MusicPlayer] Ошибка при отключении: {e}")
            finally:
                self.voice_client = None
                self.last_disconnect_time = asyncio.get_event_loop().time()

    async def get_voice_channel(self) -> disnake.VoiceChannel | None:
        """Получаем текущую голосовую руму из Redis по ключу"""
        async with RedisManager() as redis:
            try:
                record = await redis.load(SpeakerVoice, key="random_channel")
            except Exception as e:
                print(f"[MusicPlayer] Ошибка при загрузке из Redis: {e}")
                return None

        if not record or not record.random_channel_id:
            print("[MusicPlayer] Голосовая рума не найдена в Redis")
            return None
        channel = self.bot.get_channel(int(record.random_channel_id))
        if not isinstance(channel, disnake.VoiceChannel):
            print("[MusicPlayer] Канал в Redis не является голосовым")
            return None
        return channel

    async def connect_and_play(self):
        async with self.connecting_lock:
            if self.integration_cog is None:
                self.integration_cog = self.bot.get_cog("MusicIntegration")

            voice_channel = await self.get_voice_channel()
            if not voice_channel:
                print("[MusicPlayer] Канал не найден или не является голосовым")
                return

            if self.last_disconnect_time is not None:
                elapsed = asyncio.get_event_loop().time() - self.last_disconnect_time
                if elapsed < 30:
                    await asyncio.sleep(30 - elapsed)

            try:
                if self.voice_client and self.voice_client.is_connected():
                    if self.voice_client.channel.id != voice_channel.id:
                        await self.voice_client.move_to(voice_channel)
                else:
                    await self.force_disconnect()
                    self.voice_client = await voice_channel.connect()

                if self.integration_cog:
                    await self.integration_cog.send_or_update_message("Ожидание музыки...")

            except disnake.ClientException as e:
                print(f"[MusicPlayer] Ошибка подключения к голосовому каналу: {e}")
                return

            await asyncio.sleep(5)

            files = [f for f in os.listdir(self.music_folder) if f.lower().endswith((".mp3", ".wav", ".ogg", ".aac"))]
            if not files:
                print("[MusicPlayer] Музыкальные файлы не найдены.")
                return

            while True:
                if self.is_disconnected():
                    if self.integration_cog:
                        await self.integration_cog.delete_message()
                    self.last_disconnect_time = asyncio.get_event_loop().time()
                    await self.force_disconnect()
                    break

                file = random.choice(files)
                path = os.path.join(self.music_folder, file)

                if self.integration_cog:
                    await self.integration_cog.send_or_update_message(file)

                try:
                    source = disnake.FFmpegPCMAudio(
                        path,
                        before_options='-hide_banner',
                        options='-loglevel error',
                        stderr=subprocess.DEVNULL
                    )
                    player = disnake.PCMVolumeTransformer(source, volume=self.volume)
                    self.voice_client.play(player)
                except Exception as e:
                    print(f"[MusicPlayer] Ошибка воспроизведения файла {file}: {e}")
                    self.last_disconnect_time = asyncio.get_event_loop().time()
                    await self.force_disconnect()
                    break

                while self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
                    await asyncio.sleep(1)

    @tasks.loop(seconds=30)
    async def auto_reconnect(self):
        voice_channel = await self.get_voice_channel()
        if voice_channel and self.is_disconnected():
            if self.integration_cog:
                await self.integration_cog.delete_message()
            await self.connect_and_play()

    @auto_reconnect.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
