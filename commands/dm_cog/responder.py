import disnake
from disnake.ext import commands
from BANNED_FILES.config import Community_Image, Embed_Color, RedisManager
from datetime import datetime, timedelta
from redis_storage.dm_message import DMLogEntry
from pytz import timezone

moscow_tz = timezone("Europe/Moscow")

class DMResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.redis = RedisManager()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return

        if isinstance(message.channel, disnake.DMChannel):
            user_id = str(message.author.id)

            async with self.redis:
                entry = await self.redis.load(DMLogEntry, user_id)

                if not entry:
                    # Отправляем ответ
                    file = disnake.File(Community_Image, filename="community.png")
                    embed = disnake.Embed(
                        title="<:aicomment:1390972485410881588> Штабное сообщение от Сержанта",
                        description=(
                            "Сержант в настоящий момент **задействован** на основном сервере. "
                            "Ответ временно невозможен, **благодарим** за понимание.\n\n"
                            ">>> Если ваш **вопрос** важен — можете повторно его отправить, и я обязательно **передам** сообщение адмиралу базы."
                        ),
                        color=self.embed_color
                    )
                    embed.add_field(
                        name="<:aitag:1390972454465175624> Цель операции:",
                        value="[Присоединиться к серверу](https://discord.gg/nQGvVAEw5r)",
                        inline=False
                    )
                    embed.set_image(url="attachment://community.png")
                    embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
                    await message.channel.send(embed=embed, file=file)

                    # Московское время в ISO формате
                    now_msk = datetime.now(moscow_tz).isoformat()

                    # Создаём новую запись с московским временем
                    entry = DMLogEntry(
                        user_id=user_id,
                        username=f"{message.author.name}",
                        content=message.content,
                        timestamp=now_msk
                    )
                    await self.redis.save(entry, user_id, ttl=timedelta(minutes=45))
