import os
import random
import asyncio
import subprocess

import disnake
from disnake.ext import commands, tasks
import yt_dlp

from BANNED_FILES.config import Embed_Color, Music_Folder, Volume_Music, RedisManager

from redis_storage.speaker_voice import SpeakerVoice


class _YtdlpLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


COOKIES_FILE = os.path.join(
    os.getcwd(),
    "youtube_cookies.txt",
)

_YTDLP_BASE_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "logger": _YtdlpLogger(),
}

YTDLP_ANDROID_OPTIONS = {
    **_YTDLP_BASE_OPTIONS,
    "extractor_args": {
        "youtube": {
            "player_client": ["android"],
        },
    },
}

YTDLP_COOKIES_OPTIONS = {
    **_YTDLP_BASE_OPTIONS,
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"],
        },
    },
}

if os.path.exists(COOKIES_FILE):
    YTDLP_COOKIES_OPTIONS["cookiefile"] = COOKIES_FILE

_YTDLP_ATTEMPTS = [YTDLP_ANDROID_OPTIONS]

if os.path.exists(COOKIES_FILE):
    _YTDLP_ATTEMPTS.append(YTDLP_COOKIES_OPTIONS)


FFMPEG_BEFORE_OPTIONS = (
    "-reconnect 1 "
    "-reconnect_streamed 1 "
    "-reconnect_delay_max 5 "
    "-hide_banner"
)


class MusicPlayer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.voice_client: disnake.VoiceClient | None = None

        self.music_folder = Music_Folder
        self.volume = Volume_Music

        self.integration_cog = None

        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

        self.last_disconnect_time: float | None = None

        self.connecting_lock = asyncio.Lock()

        self.custom_queue: asyncio.Queue = asyncio.Queue(
            maxsize=1
        )

        self.custom_active = False

        self.auto_reconnect.start()

    def is_disconnected(self) -> bool:
        return (
            self.voice_client is None
            or not self.voice_client.is_connected()
            or self.voice_client.channel is None
        )

    def is_custom_busy(self) -> bool:
        return (
            not self.custom_queue.empty()
            or self.custom_active
        )

    async def _send_embed(
        self,
        channel: disnake.abc.Messageable,
        title: str,
        description: str,
        delete_after: float | None = None,
    ):
        embed = disnake.Embed(
            title=title,
            description=description,
            color=self.embed_color,
        )

        try:
            await channel.send(
                embed=embed,
                delete_after=delete_after,
            )
        except Exception:
            pass

    async def submit_custom_track(
        self,
        url: str,
        requester: disnake.Member,
    ):
        if self.is_disconnected():
            return (
                False,
                "Сержант сейчас не в эфире.",
            )

        if self.is_custom_busy():
            return (
                False,
                "Текущий эфир **уже занят** другой композицией. **Дождитесь** окончания передачи, и после этого сможете **поставить свой** трек в очередь.",
            )

        try:
            self.custom_queue.put_nowait(
                (url, requester)
            )

        except asyncio.QueueFull:
            return (
                False,
                "Текущий эфир **уже занят** другой композицией. **Дождитесь** окончания передачи, и после этого сможете **поставить свой** трек в очередь.",
            )

        return (
            True,
            "Композиция **внесена** в очередь и выйдет **в эфир** сразу после завершения текущей передачи.",
        )

    def _extract_sync(self, url: str):
        last_error: Exception | None = None

        for options in _YTDLP_ATTEMPTS:
            try:
                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(
                        url,
                        download=False,
                    )

                    return (
                        info["title"],
                        info["url"],
                    )

            except Exception as e:
                last_error = e
                continue

        raise last_error

    async def _extract_youtube(self, url: str):
        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(
            None,
            self._extract_sync,
            url,
        )

    async def force_disconnect(self):
        if self.voice_client:
            try:
                await self.voice_client.disconnect(
                    force=True
                )

                self.voice_client.cleanup()

            except Exception:
                pass

            finally:
                self.voice_client = None

                self.last_disconnect_time = (
                    asyncio.get_event_loop().time()
                )

    async def get_voice_channel(
        self,
    ) -> disnake.VoiceChannel | None:

        async with RedisManager() as redis:
            try:
                record = await redis.load(
                    SpeakerVoice,
                    key="random_channel",
                )

            except Exception:
                return None

        if (
            not record
            or not record.random_channel_id
        ):
            return None

        channel = self.bot.get_channel(
            int(record.random_channel_id)
        )

        if not isinstance(
            channel,
            disnake.VoiceChannel,
        ):
            return None

        return channel

    async def _notify_integration(
        self,
        track_name: str,
        custom: bool = False,
        requester: disnake.Member | None = None,
    ):

        if not self.integration_cog or not self.voice_client:
            return

        await self.integration_cog.send_or_update_message(
            track_name,
            channel=self.voice_client.channel,
            custom=custom,
            requester=requester,
        )

    async def _play_and_wait(
        self,
        source: disnake.AudioSource,
    ):
        player = disnake.PCMVolumeTransformer(
            source,
            volume=self.volume,
        )

        self.voice_client.play(player)

        while (
            self.voice_client
            and (
                self.voice_client.is_playing()
                or self.voice_client.is_paused()
            )
        ):
            await asyncio.sleep(1)

    async def _play_custom_track(
        self,
        url: str,
        requester: disnake.Member,
    ):
        self.custom_active = True

        try:
            try:
                title, stream_url = (
                    await self._extract_youtube(url)
                )

            except Exception as e:
                print(f"[MusicPlayer] yt-dlp extract failed: {e!r}")

                channel = (
                    self.voice_client.channel
                    if self.voice_client
                    else None
                )

                if channel:
                    await self._send_embed(
                        channel=channel,
                        title="<:musicsquareremove:1535597559911817286> Ошибка воспроизведения",
                        description=(
                            f"Лейтенант {requester.mention}, **трек не удалось загрузить**. Заявка отклонена системой вещания. "
                            "Попробуйте передать другую ссылку на YouTube."
                        ),
                        delete_after=15,
                    )

                return

            await self._notify_integration(
                title,
                custom=True,
                requester=requester,
            )

            try:
                source = disnake.FFmpegPCMAudio(
                    stream_url,
                    before_options=FFMPEG_BEFORE_OPTIONS,
                    options="-loglevel error -vn",
                    stderr=subprocess.DEVNULL,
                )

                await self._play_and_wait(
                    source
                )

            except Exception:
                self.last_disconnect_time = (
                    asyncio.get_event_loop().time()
                )

                await self.force_disconnect()

        finally:
            self.custom_active = False

    async def connect_and_play(self):
        async with self.connecting_lock:

            if self.integration_cog is None:
                self.integration_cog = (
                    self.bot.get_cog(
                        "MusicIntegration"
                    )
                )

            voice_channel = (
                await self.get_voice_channel()
            )

            if not voice_channel:
                return

            if self.last_disconnect_time is not None:
                elapsed = (
                    asyncio.get_event_loop().time()
                    - self.last_disconnect_time
                )

                if elapsed < 30:
                    await asyncio.sleep(
                        30 - elapsed
                    )

            try:
                if (
                    self.voice_client
                    and self.voice_client.is_connected()
                ):
                    if (
                        self.voice_client.channel.id
                        != voice_channel.id
                    ):
                        await self.voice_client.move_to(
                            voice_channel
                        )

                else:
                    await self.force_disconnect()

                    self.voice_client = (
                        await voice_channel.connect()
                    )

                await self._notify_integration(
                    "Ожидание музыки..."
                )

            except disnake.ClientException:
                return

            await asyncio.sleep(5)

            try:
                files = [
                    f
                    for f in os.listdir(
                        self.music_folder
                    )
                    if f.lower().endswith(
                        (
                            ".mp3",
                            ".wav",
                            ".ogg",
                            ".aac",
                        )
                    )
                ]

            except OSError:
                return

            if not files:
                return

            while True:

                if self.is_disconnected():
                    if self.integration_cog:
                        await self.integration_cog.delete_message()

                    self.last_disconnect_time = (
                        asyncio.get_event_loop().time()
                    )

                    await self.force_disconnect()

                    break

                if not self.custom_queue.empty():
                    url, requester = (
                        self.custom_queue.get_nowait()
                    )

                    await self._play_custom_track(
                        url,
                        requester,
                    )

                    continue

                file = random.choice(files)

                path = os.path.join(
                    self.music_folder,
                    file,
                )

                await self._notify_integration(file)

                try:
                    source = disnake.FFmpegPCMAudio(
                        path,
                        before_options="-hide_banner",
                        options="-loglevel error",
                        stderr=subprocess.DEVNULL,
                    )

                    await self._play_and_wait(
                        source
                    )

                except Exception:
                    self.last_disconnect_time = (
                        asyncio.get_event_loop().time()
                    )

                    await self.force_disconnect()

                    break

    @tasks.loop(seconds=30)
    async def auto_reconnect(self):
        voice_channel = (
            await self.get_voice_channel()
        )

        if (
            voice_channel
            and self.is_disconnected()
        ):
            if self.integration_cog:
                await self.integration_cog.delete_message()

            await self.connect_and_play()

    @auto_reconnect.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
