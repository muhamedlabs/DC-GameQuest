import os
import asyncio
import disnake
from disnake.ext import commands
from disnake.errors import DiscordServerError, HTTPException
from BANNED_FILES.config import Music_Image, Embed_Color, RedisManager
from redis_storage.speaker_voice import SpeakerVoice

class MusicIntegration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message: disnake.Message | None = None
        self.embed_image_filename = os.path.basename(Music_Image)
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    async def get_voice_channel(self) -> disnake.abc.GuildChannel | None:
        """Получаем текущую голосовую руму из Redis по ключу"""
        async with RedisManager() as redis:
            try:
                record = await redis.load(SpeakerVoice, key="random_channel")
            except Exception as e:
                print(f"[MusicIntegration] Ошибка при загрузке из Redis: {e}")
                return None

        if not record or not record.random_channel_id:
            print("[MusicIntegration] Голосовая рума не найдена в Redis")
            return None

        channel = self.bot.get_channel(int(record.random_channel_id))
        if not isinstance(channel, disnake.VoiceChannel):
            print("[MusicIntegration] Канал в Redis не является голосовым")
            return None
        return channel

    def _clean_track_name(self, track_name: str) -> str:
        """Удаляем расширение файла из названия трека"""
        return os.path.splitext(track_name)[0]

    async def send_or_update_message(self, track_name: str):
        channel = await self.get_voice_channel()
        if channel is None:
            return

        clean_name = self._clean_track_name(track_name)
        file = disnake.File(Music_Image, filename=self.embed_image_filename)

        embed = disnake.Embed(
            title="<:playlis:1390972178622582856> Сейчас в эфире — наш персональный хит!",
            description=f"Тот самый бит, от которого дрожат стёкла:\n> **{clean_name}**",
            color=self.embed_color
        )
        embed.set_image(url=f"attachment://{self.embed_image_filename}")
        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

        MAX_RETRIES = 3

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if self.message is None:
                    self.message = await channel.send(embed=embed, file=file)
                else:
                    await self.message.edit(embed=embed)
                break
            except DiscordServerError as e:
                if e.status == 503:
                    print(f"[MusicIntegration] Discord недоступен (503). Попытка {attempt} из {MAX_RETRIES}...")
                    await asyncio.sleep(2 * attempt)
                else:
                    print(f"[MusicIntegration] DiscordServerError: {e}")
                    break
            except disnake.NotFound:
                print("[MusicIntegration] Сообщение удалено, создаём заново.")
                try:
                    self.message = await channel.send(embed=embed, file=file)
                except Exception as e:
                    print(f"[MusicIntegration] Ошибка повторной отправки: {e}")
                break
            except HTTPException as e:
                print(f"[MusicIntegration] HTTPException: {e}")
                break
            except Exception as e:
                print(f"[MusicIntegration] Неизвестная ошибка при отправке сообщения: {e}")
                break

    async def delete_message(self):
        if self.message:
            try:
                await self.message.delete()
            except disnake.NotFound:
                pass
            except Exception as e:
                print(f"[MusicIntegration] Ошибка удаления сообщения: {e}")
            finally:
                self.message = None
