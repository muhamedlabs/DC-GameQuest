import disnake
from disnake.ext import commands
import aiohttp
import logging
from BANNED_FILES.config import LOG_VOICE_THREAD_ID, Embed_Color
from commands.information_cog.time import current_time as get_current_time, parse_time


class VoiceLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_thread_id = LOG_VOICE_THREAD_ID
        self.webhook_cache = {}
        self.bot_avatar: bytes = b""
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.bot.loop.create_task(self.prepare())

    async def prepare(self):
        await self.bot.wait_until_ready()
        await self.cache_bot_avatar()

    async def cache_bot_avatar(self):
        url = self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    self.bot_avatar = await resp.read()
        except Exception as e:
            logging.error(f"Ошибка при загрузке аватарки бота: {e}")

    async def get_or_create_webhook(self, thread: disnake.Thread) -> disnake.Webhook:
        webhook_name = f"{self.bot.user.name}_Voice"
        if thread.id in self.webhook_cache:
            return self.webhook_cache[thread.id]

        try:
            # Получаем родительский канал ветки
            parent_channel = thread.parent
            if not parent_channel:
                logging.error(f"Не удалось получить родительский канал для ветки {thread.id}")
                return None

            # Получаем вебхуки из родительского канала
            webhooks = await parent_channel.webhooks()
            for wh in webhooks:
                if wh.name == webhook_name:
                    self.webhook_cache[thread.id] = wh
                    return wh

            # Создаём вебхук в родительском канале
            webhook = await parent_channel.create_webhook(name=webhook_name, avatar=self.bot_avatar)
            self.webhook_cache[thread.id] = webhook
            return webhook
        except disnake.Forbidden:
            logging.error(f"Нет прав создавать вебхуки в канале {thread.parent.id}")
        except Exception as e:
            logging.error(f"Ошибка при получении или создании вебхука: {e}")

        return None

    def get_rank(self, member: disnake.Member) -> str:
        return "Сержант" if member.bot else "Лейтенант"

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        embed = disnake.Embed(color=self.embed_color)

        current_time_str = get_current_time()

        rank = self.get_rank(member)
        user_mention = f"<@{member.id}>"

        def channel_mention(ch):
            return f"<#{ch.id}>" if ch else "—"

        if not before.channel and after.channel:
            embed.title = "<:callcalling:1390972394268659753> Подключение к оперативной сети"
            embed.description = (
                f"{rank} {user_mention} десантировался в сектор. Оружие заряжено, юмор — тоже.\n\n"
                f"<:channel:1390972349385281630> **Сектор:** {channel_mention(after.channel)}\n"
                f"<:calendar:1390972430780203058> **Время подключения:** {current_time_str}\n\n"
            )
        elif before.channel and not after.channel:
            embed.title = "<:callslash:1390972370508054578> Исчез в радиопомехах"
            embed.description = (
                f"{rank} {user_mention} вышел из радиуса действия. Возможно, перешёл на другую частоту.\n\n"
                f"<:channel:1390972349385281630> **Сектор:** {channel_mention(before.channel)}\n"
                f"<:calendar:1390972430780203058> **Время отключения:** {current_time_str}\n\n"
            )
        elif before.channel != after.channel:
            embed.title = "<:calladd:1390972416452202596> Срочная эвакуация в другой войс"
            embed.description = (
                f"{rank} {user_mention} рванул в другой сектор, как будто за ним гнался ПВО.\n\n"
                f"<:channel:1390972349385281630> **Старый сектор:** {channel_mention(before.channel)}\n"
                f"<:channeladd:1390972291604545556> **Новый сектор:** {channel_mention(after.channel)}\n"
                f"<:calendar:1390972430780203058> **Время переключения:** {current_time_str}\n\n"
            )
        else:
            return

        await self.send_voice_log(member.guild, embed)

    async def send_voice_log(self, guild: disnake.Guild, embed: disnake.Embed):
        # Получаем ветку по ID из конфига
        thread = guild.get_thread(self.log_thread_id)
        
        # Проверяем, что это действительно ветка
        if not isinstance(thread, disnake.Thread):
            logging.error(f"Объект с ID {self.log_thread_id} не является веткой")
            return

        if not self.bot_avatar:
            await self.cache_bot_avatar()

        webhook = await self.get_or_create_webhook(thread)
        if webhook is None:
            logging.error("Вебхук не получен, лог не отправлен")
            return

        try:
            # Отправляем именно в ветку, указывая thread параметр
            await webhook.send(
                embed=embed,
                username=f"{self.bot.user.name}_Voice",
                avatar_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
                allowed_mentions=disnake.AllowedMentions(users=True),
                thread=thread  # <-- КЛЮЧЕВОЙ МОМЕНТ: указываем ветку для отправки
            )
        except disnake.Forbidden:
            logging.error("Недостаточно прав для отправки сообщения через вебхук")
        except Exception as e:
            logging.error(f"Ошибка при отправке лога через вебхук: {e}")
