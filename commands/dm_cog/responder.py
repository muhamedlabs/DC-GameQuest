import disnake
from disnake.ext import commands
from BANNED_FILES.config import Community_Image, Embed_Color, RedisManager
from commands.information_cog.time import hours_time
from datetime import timedelta
from redis_storage.dm_message import DMLogEntry

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
                    file = disnake.File(Community_Image, filename="community.png")
                    embed = disnake.Embed(
                        title="<:aicomment:1390972485410881588> Штабное сообщение от сержанта",
                        description=(
                            ">>> Сержант в настоящий момент **задействован** на основном сервере. "
                            "Ответ временно невозможен, **благодарим** за понимание."
                        ),
                        color=self.embed_color
                    )

                    embed.add_field(
                        name="<:aihospital:1399050596962668634> Командный центр поддержки:",
                        value=(
                            "Если ваш **рапорт** критичен — можете повторно его отправить, и оно будет обязательно **передано** адмиралу базы. "
                            "Мы не оставим вас без поддержки!"
                        ),
                        inline=False
                    )

                    embed.add_field(
                        name="<:aitag:1390972454465175624> Стратегическая цель миссии:",
                        value="[Присоединиться к штабу оперативного управления](https://discord.gg/nQGvVAEw5r)",
                        inline=False
                    )
                    embed.set_image(url="attachment://community.png")
                    embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
                    await message.channel.send(embed=embed, file=file)

                    entry = DMLogEntry(
                        user_id=user_id,
                        username=str(message.author.name),
                        content=message.content,
                        timestamp=hours_time
                    )
                    await self.redis.save(entry, user_id, ttl=timedelta(minutes=45))