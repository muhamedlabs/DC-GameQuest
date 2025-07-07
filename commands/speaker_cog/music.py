import os
import random
import asyncio
import subprocess
import disnake
import logging
from disnake.ext import commands, tasks
from BANNED_FILES.config import SPEAKER_VOICE_ID, Music_Folder, Volume_Music

logging.getLogger("disnake.voice_client").setLevel(logging.CRITICAL)

class MusicPlayer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_client: disnake.VoiceClient | None = None
        self.music_folder = Music_Folder
        self.volume = Volume_Music
        # self.ffmpeg_path = Ffmpeg_Path
        self.integration_cog = None
        self.last_disconnect_time: float | None = None
        self.auto_reconnect.start()

    def is_disconnected(self) -> bool:
        return (
            self.voice_client is None
            or not self.voice_client.is_connected()
            or self.voice_client.channel is None
        )

    async def connect_and_play(self):
        if self.integration_cog is None:
            self.integration_cog = self.bot.get_cog("MusicIntegration")

        voice_channel = self.bot.get_channel(SPEAKER_VOICE_ID)
        if not isinstance(voice_channel, disnake.VoiceChannel):
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
                self.voice_client = await voice_channel.connect()

            if self.integration_cog:
                await self.integration_cog.send_or_update_message("Ожидание пожалуста музыки....")
        except disnake.ClientException:
            return

        await asyncio.sleep(15)

        files = [f for f in os.listdir(self.music_folder) if f.endswith((".mp3", ".wav", ".ogg", ".aac"))]
        if not files:
            return

        while True:
            if self.is_disconnected():
                if self.integration_cog:
                    await self.integration_cog.delete_message()
                self.last_disconnect_time = asyncio.get_event_loop().time()
                break

            file = random.choice(files)

            if self.integration_cog:
                await self.integration_cog.send_or_update_message(file)

            try:
                source = disnake.FFmpegPCMAudio(
                    os.path.join(self.music_folder, file),
                    # executable=self.ffmpeg_path,
                    before_options='-hide_banner',
                    options='-loglevel error',
                    stderr=subprocess.DEVNULL
                )
                player = disnake.PCMVolumeTransformer(source, volume=self.volume)

                self.voice_client.play(player)
            except Exception:
                self.last_disconnect_time = asyncio.get_event_loop().time()
                break

            while self.voice_client.is_playing() or self.voice_client.is_paused():
                await asyncio.sleep(1)

    @tasks.loop(seconds=30)
    async def auto_reconnect(self):
        voice_channel = self.bot.get_channel(SPEAKER_VOICE_ID)
        if isinstance(voice_channel, disnake.VoiceChannel):
            if self.is_disconnected():
                if self.integration_cog:
                    await self.integration_cog.delete_message()
                await self.connect_and_play()

    @auto_reconnect.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
