import disnake
from disnake.ext import commands
import aiohttp
import logging
from datetime import datetime, timedelta, timezone
from BANNED_FILES.config import LOG_ROLE_THREAD_ID, Embed_Color
from commands.information_cog.time import current_time as get_current_time, parse_time


class RoleUpdateLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_thread_id = LOG_ROLE_THREAD_ID
        self.webhook_cache = {}
        self.bot_avatar: bytes = b""
        self.bot.loop.create_task(self.prepare())
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

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
            logging.error(f"[Avatar] Ошибка при загрузке аватарки бота: {e}")

    async def get_or_create_webhook(self, thread: disnake.Thread) -> disnake.Webhook:
        webhook_name = f"{self.bot.user.name}_Roles"
        if thread.id in self.webhook_cache:
            return self.webhook_cache[thread.id]

        try:
            # Получаем родительский канал ветки
            parent_channel = thread.parent
            if not parent_channel:
                logging.error(f"[Webhook] Не удалось получить родительский канал для ветки {thread.id}")
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
            logging.error(f"[Webhook] Нет прав создавать вебхуки в канале {thread.parent.id}")
        except Exception as e:
            logging.error(f"[Webhook] Ошибка при получении или создании вебхука: {e}")

        return None

    def get_rank(self, member: disnake.Member) -> str:
        return "сержант" if member.bot else "лейтенант"

    @commands.Cog.listener()
    async def on_member_update(self, before: disnake.Member, after: disnake.Member):
        # Убираем проверку на after.bot, чтобы логировать изменения у ботов тоже
        if before.roles == after.roles:
            return

        added_roles = [role.mention for role in after.roles if role not in before.roles]
        removed_roles = [role.mention for role in before.roles if role not in after.roles]

        if not added_roles and not removed_roles:
            return

        changer = None
        try:
            now = datetime.now(timezone.utc)
            async for entry in after.guild.audit_logs(limit=10, action=disnake.AuditLogAction.member_role_update):
                if entry.target.id == after.id and (now - entry.created_at).total_seconds() < 15:
                    changer = entry.user
                    break
        except Exception as e:
            logging.warning(f"[AuditLog] Ошибка при получении логов аудита: {e}")

        rank = self.get_rank(after)
        embed = disnake.Embed(color=self.embed_color)
        
        # Используем функцию current_time() из time.py
        current_time_str = get_current_time()
        
        user_mention = f"<@{after.id}>"

        embed.title = "<:securityuser:1387113332208566342> Перестановка в рядах специализация"
        embed.description = (
            f"У {rank} {user_mention} произошла **смена специализация**. "
            f"{f'Ответственность за **операцию** лежала на офицере или его прямом подчинённом: <@{changer.id}>.' if changer else 'Ответственный офицер не был зафиксирован.'}"
        )

        roles_summary = ""
        if added_roles:
            roles_summary += f"<:shieldtick:1387113358389547138> **Добавлены специализация:** {' '.join(added_roles)}\n"
        if removed_roles:
            roles_summary += f"<:shieldcross:1387113344908923125> **Удалены специализация:** {' '.join(removed_roles)}\n"
        roles_summary += f"<:calendar:1390972430780203058> **Время операции:** {current_time_str}"

        embed.add_field(name="\u200b", value=roles_summary, inline=False)  # пустой заголовок для поля

        await self.send_role_log(after.guild, embed)

    async def send_role_log(self, guild: disnake.Guild, embed: disnake.Embed):
        # Получаем ветку по ID из конфига
        thread = guild.get_thread(self.log_thread_id)
        
        # Проверяем, что это действительно ветка
        if not isinstance(thread, disnake.Thread):
            logging.error(f"[LogThread] Объект с ID {self.log_thread_id} не является веткой")
            return

        if not self.bot_avatar:
            await self.cache_bot_avatar()

        webhook = await self.get_or_create_webhook(thread)
        if webhook is None:
            logging.error("[Webhook] Вебхук не получен, лог не отправлен")
            return

        try:
            # Отправляем именно в ветку, указывая thread параметр
            await webhook.send(
                embed=embed,
                username=f"{self.bot.user.name}_Roles",
                allowed_mentions=disnake.AllowedMentions(users=True),
                thread=thread  # <-- КЛЮЧЕВОЙ МОМЕНТ: указываем ветку для отправки
            )
        except disnake.Forbidden:
            logging.error("[Webhook] Недостаточно прав для отправки сообщения через вебхук")
        except Exception as e:
            logging.error(f"[Webhook] Ошибка при отправке лога: {e}")