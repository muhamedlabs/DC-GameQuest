import disnake
from disnake.ext import commands
from datetime import datetime
from pytz import timezone
from BANNED_FILES.config import Embed_Color, RedisManager
from redis_storage.users_subscriptions import UsersSubscriptions

moscow_tz = timezone("Europe/Moscow")

class SignalSubscription(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    async def can_send_dm(self, user: disnake.User) -> bool:
        """Проверяет, может ли бот писать в ЛС"""
        try:
            await user.send(embed=disnake.Embed(
                title="✅ Проверка связи",
                description="Бот сможет отправлять вам сигналы!",
                color=self.embed_color
            ))
            return True
        except disnake.Forbidden:
            return False

    async def update_subscription(self, user: disnake.User, subscribe: bool) -> str:
        """Обновляет запись о пользователе в Redis и возвращает статус"""
        key = [str(user.id)]

        async with RedisManager() as redis:
            existing: UsersSubscriptions = await redis.load(UsersSubscriptions, key)

            # Пользователь уже подписан
            if existing and existing.subscription == "On" and subscribe:
                return "already_subscribed"

            number_canceled = (
                str(int(existing.number_canceled_subscriptions or "0") + 1)
                if existing and not subscribe
                else existing.number_canceled_subscriptions if existing else "0"
            )

            time_actions_commands = datetime.now(moscow_tz).strftime("%d.%m.%Y %H:%M:%S")

            record = UsersSubscriptions(
                user_id=str(user.id),
                username=str(user),
                subscription="On" if subscribe else "Off",  # Теперь On/Off
                time_actions_commands=time_actions_commands,
                number_canceled_subscriptions=number_canceled
            )
            await redis.save(record, key)
            return "subscribed" if subscribe else "unsubscribed"

    @commands.slash_command(name="сигнал", description="Подписка или отписка от сигналов/новостей")
    async def signal_subscription(
        self,
        inter: disnake.ApplicationCommandInteraction,
        действие: str = commands.Param(
            choices=["Подписаться", "Отписаться"], description="Выберите действие"
        )
    ):
        await inter.response.defer()  # больше не ephemeral

        subscribe = действие == "Подписаться"

        # Проверка DM для подписки только если пользователь ещё не подписан
        if subscribe:
            key = [str(inter.author.id)]
            async with RedisManager() as redis:
                existing: UsersSubscriptions = await redis.load(UsersSubscriptions, key)

            if not existing or existing.subscription != "On":
                can_dm = await self.can_send_dm(inter.author)
                if not can_dm:
                    embed = disnake.Embed(
                        title="⚠ Не удалось подписать",
                        description="Ваши личные сообщения закрыты. Разрешите боту писать и попробуйте снова.",
                        color=self.embed_color
                    )
                    return await inter.edit_original_message(embed=embed)

        status = await self.update_subscription(inter.author, subscribe)

        # Создаём эмбед с результатом
        if status == "already_subscribed":
            embed = disnake.Embed(
                title="📡 Вы уже подписаны",
                description="Вы уже получаете сигналы. Новая подписка не требуется.",
                color=self.embed_color
            )
        elif status == "subscribed":
            embed = disnake.Embed(
                title="📡 Подписка оформлена! (On)",
                description="Теперь бот будет присылать вам важные уведомления прямо в личные сообщения.",
                color=self.embed_color
            )
        else:  # unsubscribed
            embed = disnake.Embed(
                title="🔕 Вы отписались (Off)",
                description="Бот больше не будет присылать сигналы.\nРекомендуем подписаться, чтобы быть в курсе всех новостей!",
                color=self.embed_color
            )

        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        await inter.edit_original_message(embed=embed)
