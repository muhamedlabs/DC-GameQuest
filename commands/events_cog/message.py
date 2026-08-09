import disnake
from disnake.ext import commands
import logging
import aiohttp
from BANNED_FILES.config import LOG_CHANNEL_ID, Embed_Color
from commands.information_cog.time import current_time as get_current_time




class MessageLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = LOG_CHANNEL_ID
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.webhook_cache = {}
        self.bot_avatar: bytes = b""
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
            logging.error(f"[Avatar] Ошибка при загрузке аватарки бота: {e}")

    async def get_or_create_webhook(self, channel: disnake.TextChannel) -> disnake.Webhook:
        webhook_name = f"{self.bot.user.name}_Messages"
        if channel.id in self.webhook_cache:
            return self.webhook_cache[channel.id]

        try:
            webhooks = await channel.webhooks()
            for wh in webhooks:
                if wh.name == webhook_name:
                    self.webhook_cache[channel.id] = wh
                    return wh

            webhook = await channel.create_webhook(name=webhook_name, avatar=self.bot_avatar)
            self.webhook_cache[channel.id] = webhook
            return webhook
        except disnake.Forbidden:
            logging.error(f"[Webhook] Нет прав создать вебхук в канале {channel.id}")
        except Exception as e:
            logging.error(f"[Webhook] Ошибка при создании вебхука: {e}")

        return None

    def get_rank(self, member: disnake.Member) -> str:
        return "Сержант" if member.bot else "Лейтенант"

    async def send_log(self, guild, embed):
        channel = guild.get_channel(self.log_channel_id)
        if not isinstance(channel, disnake.TextChannel):
            logging.error("Канал логов не найден или не является текстовым.")
            return

        if not self.bot_avatar:
            await self.cache_bot_avatar()

        webhook = await self.get_or_create_webhook(channel)
        if webhook is None:
            logging.error("Вебхук не получен. Лог не отправлен.")
            return

        try:
            await webhook.send(
                embed=embed,
                username=f"{self.bot.user.name}_Messages",
                avatar_url=self.bot.user.avatar.url if self.bot.user.avatar else None,
                allowed_mentions=disnake.AllowedMentions.none()
            )
        except disnake.Forbidden:
            logging.error("Нет прав на отправку через вебхук.")
        except Exception as e:
            logging.error(f"Ошибка при отправке через вебхук: {e}")

    def format_message(self, content: str) -> str:
        return f"```{content[:1000]}```" if content else "—"

    @commands.Cog.listener()
    async def on_message_delete(self, message: disnake.Message):
        if not message.guild:
            return

        rank = self.get_rank(message.author)
        description = (
            f"{rank} {message.author.mention} провёл скрытную операцию и ликвидировал сообщение в секторе {message.channel.mention}.\n\n"
            + (f"<:text:1387180247123890196> **Перехваченное сообщение:**\n{self.format_message(message.content)}\n" if message.content else "")
            + f"<:calendar:1390972430780203058> **Время операции:** {get_current_time()} по МСК"
        )

        embed = disnake.Embed(
            title="<:firstline:1387180213225390182> Отчёт о ликвидации сообщения",
            description=description,
            color=self.embed_color
        )

        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: disnake.Message, after: disnake.Message):
        if not before.guild or before.content == after.content:
            return

        rank = self.get_rank(before.author)
        description = (
            f"{rank} {before.author.mention} провёл скрытную операцию и внёс корректировки в сообщение в секторе {before.channel.mention}.\n\n"
            f"<:text:1387180247123890196> **Исходное сообщение:**\n{self.format_message(before.content)}\n"
            f"<:smallcaps:1387180229763661905> **Модифицированное сообщение:**\n{self.format_message(after.content)}\n"
            f"<:calendar:1390972430780203058> **Время фиксации:** {get_current_time()} по МСК"
        )

        embed = disnake.Embed(
            title="<:firstline:1387180213225390182> Отчёт о правках сообщения",
            description=description,
            color=self.embed_color
        )

        await self.send_log(before.guild, embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        for msg in messages:
            if not msg.guild:
                continue

            rank = self.get_rank(msg.author)
            description = (
                f"{rank} {msg.author.mention} попал под массовую зачистку сообщений в секторе {msg.channel.mention}.\n\n"
                + (f"<:text:1387180247123890196> **Перехвачено сообщение:**\n{self.format_message(msg.content)}\n\n" if msg.content else "")
                + f"<:calendar:1390972430780203058> **Время операции:** {get_current_time()} по МСК"
            )

            embed = disnake.Embed(
                title="<:firstline:1387180213225390182> Отчёт о массовой зачистке",
                description=description,
                color=self.embed_color
            )

            await self.send_log(msg.guild, embed)
