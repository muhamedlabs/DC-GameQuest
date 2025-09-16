import disnake
from disnake.ext import commands
from datetime import datetime
from pytz import timezone
import asyncio
from BANNED_FILES.config import Embed_Color, RedisManager, VIDEO_CHANNEL_ID
from redis_storage.users_subscriptions import UsersSubscriptions

moscow_tz = timezone("Europe/Moscow")

class SignalSender(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    async def get_subscribed_users(self):
        """Возвращает всех пользователей с subscription == 'Подписан'"""
        async with RedisManager() as redis:
            users = await redis.load_many(UsersSubscriptions, key="*")
            subscribed_users = [u.user_id for u in users if u.subscription == "Подписан"]
        return subscribed_users

    async def send_signal_dm(self, user_id: str, embed: disnake.Embed):
        """Отправка эмбеда пользователю до 3 попыток"""
        user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
        if not user:
            return
        for _ in range(3):
            try:
                await user.send(embed=embed)
                return  # успешно отправлено
            except disnake.Forbidden:
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(1)
        return  # Не удалось после 3 попыток — пропускаем

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        # Игнорируем сообщения не из канала сигналов
        if message.channel.id != VIDEO_CHANNEL_ID:
            return

        subscribed_users = await self.get_subscribed_users()
        if not subscribed_users:
            return

        # Заготовленный эмбед для всех сообщений
        embed = disnake.Embed(
            title="📢 Новый сигнал!",
            description="Важное уведомление от Game Quest. Следите за обновлениями!",
            color=self.embed_color,
            timestamp=datetime.now(moscow_tz)
        )

        # Отправка всем подписанным
        for user_id in subscribed_users:
            await self.send_signal_dm(user_id, embed)
