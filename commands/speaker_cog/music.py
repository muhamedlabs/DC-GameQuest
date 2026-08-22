import os
import random
import asyncio
import subprocess
import shutil

import disnake
from disnake.ext import commands, tasks
import yt_dlp

from BANNED_FILES.config import Embed_Color, Community_Image, Music_Folder, Volume_Music, Music_Track, Delete_Times, RedisManager

from redis_storage.speaker_voice import SpeakerVoice


class _YtdlpLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def _find_project_root(start_path: str) -> str:
    current = start_path

    while True:
        if os.path.exists(os.path.join(current, "main.py")):
            return current

        parent = os.path.dirname(current)

        if parent == current:
            return start_path

        current = parent


COOKIES_FILE = os.path.join(
    _find_project_root(
        os.path.dirname(os.path.abspath(__file__))
    ),
    "youtube_cookies.txt",
)

_DENO_PATH = (
    shutil.which("deno")
    or os.path.expanduser("~/.deno/bin/deno")
)

_YTDLP_BASE_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "logger": _YtdlpLogger(),
    "remote_components": ["ejs:github"],
    "js_runtimes": {"deno": {"path": _DENO_PATH}},
    "geo_bypass": True,
}

YTDLP_ANDROID_OPTIONS = {
    **_YTDLP_BASE_OPTIONS,
    "extractor_args": {
        "youtube": {
            "player_client": ["android"],
        },
    },
}

YTDLP_IOS_OPTIONS = {
    **_YTDLP_BASE_OPTIONS,
    "extractor_args": {
        "youtube": {
            "player_client": ["ios"],
        },
    },
}

YTDLP_WEB_OPTIONS = {
    **_YTDLP_BASE_OPTIONS,
    "extractor_args": {
        "youtube": {
            "player_client": ["web"],
        },
    },
}

YTDLP_COOKIES_OPTIONS = {
    **_YTDLP_BASE_OPTIONS,
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "ios", "web"],
        },
    },
}

if os.path.exists(COOKIES_FILE):
    YTDLP_COOKIES_OPTIONS["cookiefile"] = COOKIES_FILE

_YTDLP_ATTEMPTS = [
    YTDLP_ANDROID_OPTIONS,
    YTDLP_IOS_OPTIONS,
    YTDLP_WEB_OPTIONS,
]

if os.path.exists(COOKIES_FILE):
    _YTDLP_ATTEMPTS.append(YTDLP_COOKIES_OPTIONS)


FFMPEG_BEFORE_OPTIONS = (
    "-reconnect 1 "
    "-reconnect_streamed 1 "
    "-reconnect_delay_max 5 "
    "-hide_banner"
)

YTDLP_EXTRACT_TIMEOUT = 20


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

    def cog_unload(self):
        self.auto_reconnect.cancel()
        asyncio.create_task(self.force_disconnect())

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
        image_path: str | None = None,
    ):
        embed = disnake.Embed(
            title=title,
            description=description,
            color=self.embed_color,
        )

        file = None

        if image_path and os.path.exists(image_path):
            image_filename = os.path.basename(image_path)

            file = disnake.File(
                image_path,
                filename=image_filename,
            )

            embed.set_image(
                url=f"attachment://{image_filename}"
            )

        try:
            await channel.send(
                embed=embed,
                file=file,
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
                "Сержант сейчас не в эфире",
            )

        if self.is_custom_busy():
            return (
                False,
                "Текущий эфир **уже занят** другой композицией. **Дождитесь** окончания передачи, и после этого сможете **поставить свой** трек в очередь",
            )

        try:
            self.custom_queue.put_nowait(
                (url, requester)
            )

        except asyncio.QueueFull:
            return (
                False,
                "Текущий эфир **уже занят** другой композицией. **Дождитесь** окончания передачи, и после этого сможете **поставить свой** трек в очередь",
            )

        return (
            True,
            "Композиция **внесена** в очередь и выйдет **в эфир** сразу после завершения текущей передачи",
        )

    def _extract_single_sync(self, url: str):
        last_error: Exception | None = None

        for options in _YTDLP_ATTEMPTS:
            try:
                with yt_dlp.YoutubeDL({**options, "noplaylist": True}) as ydl:
                    info = ydl.extract_info(
                        url,
                        download=False,
                    )

                    return (
                        info.get("title") or "Без названия",
                        info["url"],
                    )

            except Exception as e:
                last_error = e
                continue

        raise last_error

    async def _extract_single(self, url: str):
        loop = asyncio.get_event_loop()

        return await asyncio.wait_for(
            loop.run_in_executor(
                None,
                self._extract_single_sync,
                url,
            ),
            timeout=YTDLP_EXTRACT_TIMEOUT,
        )

    def _extract_playlist_urls_sync(self, url: str) -> list[str]:
        last_error: Exception | None = None

        for options in _YTDLP_ATTEMPTS:
            flat_options = {
                **options,
                "noplaylist": False,
                "extract_flat": "in_playlist",
                "playlistend": Music_Track,
            }

            try:
                with yt_dlp.YoutubeDL(flat_options) as ydl:
                    info = ydl.extract_info(
                        url,
                        download=False,
                    )

            except Exception as e:
                last_error = e
                continue

            entries = info.get("entries")

            if entries:
                urls = [
                    (entry.get("url") or entry.get("webpage_url"))
                    for entry in entries
                    if entry and (entry.get("url") or entry.get("webpage_url"))
                ]

                if not urls:
                    raise ValueError(
                        "Плейлист пуст или все видео недоступны."
                    )

                return urls

            return [info.get("webpage_url") or url]

        raise last_error

    async def _extract_playlist_urls(self, url: str):
        loop = asyncio.get_event_loop()

        return await asyncio.wait_for(
            loop.run_in_executor(
                None,
                self._extract_playlist_urls_sync,
                url,
            ),
            timeout=YTDLP_EXTRACT_TIMEOUT,
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
                track_urls = await self._extract_playlist_urls(url)

            except Exception as e:
                print(f"[MusicPlayer] yt-dlp playlist extract failed: {e!r}")

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
                        delete_after=Delete_Times,
                        image_path=Community_Image,
                    )

                return

            total = len(track_urls)

            for index, track_url in enumerate(track_urls, start=1):

                if self.is_disconnected():
                    break

                try:
                    title, stream_url = await self._extract_single(track_url)

                except Exception as e:
                    print(
                        f"[MusicPlayer] yt-dlp resolve failed for track "
                        f"{index}/{total}: {e!r}"
                    )
                    continue

                display_title = (
                    title
                    if total == 1
                    else f"{title} ({index}/{total})"
                )

                await self._notify_integration(
                    display_title,
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

                    break

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