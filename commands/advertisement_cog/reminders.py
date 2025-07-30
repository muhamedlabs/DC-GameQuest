import os
import disnake
import asyncio
from disnake.ext import commands
from BANNED_FILES.config import CHAT_CHANNEL_ID, Embed_Color, Social_Subscription, Social_Donate, Social_Image, RedisManager
from redis_storage.promo_counter import PromoCounter


class AutoPromo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = CHAT_CHANNEL_ID

        self.message_threshold_sub = Social_Subscription
        self.message_threshold_donate = Social_Donate

        self.redis = RedisManager()
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

        self.lock = asyncio.Lock()

    async def cog_load(self):
        await self.redis.__aenter__()
        # Убрал вывод в консоль

    def cog_unload(self):
        asyncio.create_task(self.redis.__aexit__(None, None, None))
        # Убрал вывод в консоль

    async def save_counter_to_redis(self, record: PromoCounter):
        try:
            await self.redis.save(record, str(self.channel_id))
            # Убрал вывод в консоль
        except Exception:
            # Можно логировать ошибку, но без вывода в терминал
            pass

    @commands.Cog.listener()
    async def on_ready(self):
        # Можно убрать этот вывод, если не нужен
        pass

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.channel.id != self.channel_id or message.author.bot:
            return

        async with self.lock:
            record = await self.redis.load(PromoCounter, str(self.channel_id))
            if not record:
                record = PromoCounter(channel_id=str(self.channel_id), sub_counter=0, donate_counter=0)

            record.sub_counter = (record.sub_counter or 0) + 1
            record.donate_counter = (record.donate_counter or 0) + 1

            image_path = Social_Image
            if not os.path.exists(image_path):
                # Не выводим ошибку в терминал, просто пропускаем
                return

            file = disnake.File(image_path, filename="banner.jpg")
            image_url = "attachment://banner.jpg"

            sent = False

            try:
                if record.sub_counter >= self.message_threshold_sub:
                    embed = disnake.Embed(
                        title="<:aiusers:1388576262355943434> Оперативная cводка по социальным платформам",
                        description=(
                            "Товарищи лейтенанты! Команда **Game Quest** напоминает о необходимости **контроля** всех секторов информационного фронта!\n\n"
                            "<:youtube:1390972086876377192> **YouTube:** https://www.youtube.com/@GameQuest_news\n"
                            "<:tg:1388590213567221801> **Telegram:** https://t.me/GameQuest_news\n"
                            "<:dc:1388590201349079050> **Discord:** https://discord.gg/GJUuPRbN5a\n"
                            "<:vk:1390972535298068570> **ВКонтактe:** https://t.me/GameQuest_news"
                        ),
                        color=self.embed_color
                    )
                    embed.set_image(url=image_url)
                    embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
                    await message.channel.send(embed=embed, file=file)
                    record.sub_counter = 0
                    sent = True

                if record.donate_counter >= self.message_threshold_donate:
                    embed = disnake.Embed(
                        title="<:userai:1388576282538807487> Мониторинг добровольных пожертвований",
                        description=(
                            "Товарищи лейтенанты! Команда **Game Quest** напоминает что ваш вклад в операцию по развитию **укрепляет** наши позиции на информационном фронте!\n\n"
                            "<:wallet:1388579605379682438> **Patreon:**\n https://www.patreon.com/andremuhamad\n"
                            "<:wallet:1388579605379682438> **DonationAlerts:**\n https://www.donationalerts.com/r/andremuhamad"
                        ),
                        color=self.embed_color
                    )
                    embed.set_image(url=image_url)
                    embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
                    await message.channel.send(embed=embed, file=file)
                    record.donate_counter = 0
                    sent = True
            except disnake.HTTPException:
                # Без вывода ошибки в терминал
                pass

            await self.save_counter_to_redis(record)
