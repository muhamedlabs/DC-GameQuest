import disnake
import random
from disnake.ext import commands
from datetime import datetime, timezone, timedelta

from BANNED_FILES.config import RedisManager, Embed_Color, SATDAT_VOICE_ID, Selector_Image
from redis_storage.satbat_manager import SatbatManager

MSK = timezone(timedelta(hours=3))

class VoiceAutoMover(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.bot:
            return

        if not before.channel and after.channel and after.channel.id == SATDAT_VOICE_ID:
            current_channel = after.channel
            current_category = current_channel.category

            if not current_category:
                return

            voice_channels = [ch for ch in current_category.voice_channels if ch.id != current_channel.id]
            if not voice_channels:
                return

            user_key = [f"{member.id}"]

            async with RedisManager() as redis:
                user_data = await redis.load(SatbatManager, user_key)
                if not user_data:
                    user_data = SatbatManager(
                        user_id=str(member.id),
                        username=member.display_name,
                        transition_random_voice=0,
                        transitions_history={},
                        last_transition_time=None
                    )

                file = disnake.File(Selector_Image, filename="dial.png")    

                if user_data.transition_random_voice >= 5:
                    if user_data.last_transition_time:
                        dt = datetime.fromisoformat(user_data.last_transition_time)
                        now = datetime.now(MSK)
                        delta = timedelta(hours=24) - (now - dt)
                        if delta.total_seconds() < 0:
                            delta = timedelta(seconds=0)

                        hours, remainder = divmod(int(delta.total_seconds()), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        time_left = f"{hours:02d}ч {minutes:02d}м {seconds:02d}с"

                        last_time = dt.strftime("%d.%m.%Y %H:%M:%S")
                    else:
                        last_time = "неизвестно"
                        time_left = "неизвестно"

                    embed = disnake.Embed(
                        title="<:radio:1403796360708227223> Маневрирование по голосовому сектору",
                        description=(
                            f"> Лейтенант **{member.display_name}**, вы уже выполнили **{user_data.transition_random_voice}** оперативных перебросок с поддержкой **нашего** надёжного сержанта.\n\n"
                            f"<:calendar:1390972430780203058> **Последнее подключение к сектору зафиксировано:**\n ```{last_time} по МСК```\n"
                            f"<:calendar2:1388889677297352837>**Временной отсчет до восстановления боевого ресурса:**\n ```{time_left}```"
                        ),
                        color=self.embed_color
                    )
                    embed.set_image(url="attachment://dial.png")
                    embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
                    try:
                        await member.send(embed=embed, file=file)
                    except disnake.Forbidden:
                        if member.guild.system_channel:
                            await member.guild.system_channel.send(embed=embed)
                    return

                new_channel = random.choice(voice_channels)

                try:
                    await member.move_to(new_channel)
                except disnake.Forbidden:
                    return
                except Exception:
                    return

                now_msk = datetime.now(MSK).isoformat()

                user_data.transition_random_voice += 1
                user_data.username = member.display_name

                key = f"channel_id_{user_data.transition_random_voice}"
                user_data.transitions_history[key] = f"{new_channel.id} @ {now_msk}"

                user_data.last_transition_time = now_msk

                await redis.save(user_data, user_key, ttl=timedelta(hours=24))
