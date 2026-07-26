import disnake
from disnake.ext import commands
import asyncio
from BANNED_FILES.config import Embed_Color, Comments_Gif, RedisManager
from commands.information_cog.time import hours_time
from redis_storage.users_notification import UsersNotification
import os

class FirstNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.lock = asyncio.Lock()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot or message.guild is None:
            return

        user_id = str(message.author.id)
        key = [user_id]

        async with self.lock:
            async with RedisManager() as redis:
                record = await redis.load(UsersNotification, key)
                if record is not None:
                    return  # Запись уже есть, ничего не делаем

                member = message.guild.get_member(message.author.id)
                display_name = member.display_name if member else str(message.author)
                username = str(message.author)

                user_record = UsersNotification(
                    user_id=user_id,
                    username=username,
                    first_message_time=hours_time,
                    first_message_content=message.content
                )

                await redis.save(user_record, key)

        self.bot.loop.create_task(self.send_delayed_notification(message.author, display_name))

    async def send_delayed_notification(self, user: disnake.User, display_name: str):
        try:
            await asyncio.sleep(900)  # 15 минут

            embed = disnake.Embed(
                title=f"<:smart:1390972121768923166> Зафиксирован первичный радиосигнал",
                description=(
                    f"**Здравия желаю**, лейтенант **{display_name}**, вы официально подключились к боевому информационному каналу **Game Quest**. "
                    "Отныне координация операций, сбор разведданных и анализ обстановки **находятся** в вашей зоне ответственности.\n\n"
                    f"<:youtube:1390972086876377192> **YouTube:** https://www.youtube.com/@GameQuest_news\n"
                    f"<:tg:1388590213567221801> **Telegram:** https://t.me/GameQuest_news\n"
                    f"<:dc:1388590201349079050> **Discord:** https://discord.gg/GJUuPRbN5a\n"
                    f"<:vk:1390972535298068570> **ВКонтакте:** https://vk.com/GameQuest_news\n\n"
                    f"<:calendar:1390972430780203058> **Время регистрации:** {hours_time}\n"
                ),
                color=self.embed_color
            )
            embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

            gif_path = os.path.abspath(Comments_Gif)
            try:
                if os.path.exists(gif_path):
                    with open(gif_path, "rb") as gif:
                        file = disnake.File(gif, filename="messages.gif")
                        embed.set_image(url="attachment://messages.gif")
                        await user.send(embed=embed, file=file)
                else:
                    await user.send(embed=embed)
            except disnake.Forbidden:
                pass
            except Exception as e:
                print(f"[Ошибка] Не удалось отправить embed или гифку: {e}")

        except Exception as e:
            print(f"[Ошибка] send_delayed_notification для {user}: {e}")