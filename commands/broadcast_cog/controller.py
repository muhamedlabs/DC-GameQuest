import disnake
import random
from disnake.ext import commands, tasks
from datetime import datetime, timezone, timedelta

from BANNED_FILES.config import RedisManager, Embed_Color, SATDAT_VOICE_ID, Selector_Image
from redis_storage.satbat_manager import SatbatManager

MSK = timezone(timedelta(hours=3))

class VoiceAutoMover(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.veto_check_loop.start()  # Запускаем фоновый цикл проверки вето-рума

    def cog_unload(self):
        self.veto_check_loop.cancel()  # Останавливаем цикл при выгрузке когa

    async def get_user_data(self, redis, user_id: int):
        key = [f"{user_id}"]
        user_data = await redis.load(SatbatManager, key)
        if not user_data:
            user_data = SatbatManager(
                user_id=str(user_id),
                username=None,
                transition_random_voice=0,
                transitions_history={},
                last_transition_time=None,
                veto_join_time=None,
            )
        return user_data, key

    async def get_veto_data(self, redis, user_id: int):
        key = [f"veto:{user_id}"]
        veto_data = await redis.load(SatbatManager, key)
        if not veto_data:
            veto_data = SatbatManager(user_id=str(user_id), veto_join_time=None)
        return veto_data, key

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.bot:
            return

        async with RedisManager() as redis:
            # Получаем данные вето и пользователя
            veto_data, veto_key = await self.get_veto_data(redis, member.id)
            user_data, user_key = await self.get_user_data(redis, member.id)
            now_msk = datetime.now(MSK)

            # Пользователь заходит в вето-рум — сохраняем время захода
            if not before.channel and after.channel and after.channel.id == SATDAT_VOICE_ID:
                veto_data.veto_join_time = now_msk.isoformat()
                await redis.save(veto_data, veto_key, ttl=timedelta(hours=3))

                # Проверяем лимит перебросок
                current_channel = after.channel
                current_category = current_channel.category
                if not current_category:
                    return

                voice_channels = [ch for ch in current_category.voice_channels if ch.id != current_channel.id]
                if not voice_channels:
                    return

                file = disnake.File(Selector_Image, filename="dial.png")

                if user_data.transition_random_voice >= 5:
                    if user_data.last_transition_time:
                        dt = datetime.fromisoformat(user_data.last_transition_time)
                        delta = timedelta(hours=24) - (now_msk - dt)
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

                # Если лимит не превышен — перебрасываем
                new_channel = random.choice(voice_channels)
                try:
                    await member.move_to(new_channel)
                except (disnake.Forbidden, Exception):
                    return

                now_iso = now_msk.isoformat()
                user_data.transition_random_voice += 1
                user_data.username = member.display_name
                key = f"channel_id_{user_data.transition_random_voice}"
                user_data.transitions_history[key] = f"{new_channel.id} @ {now_iso}"
                user_data.last_transition_time = now_iso
                await redis.save(user_data, user_key, ttl=timedelta(hours=24))

            # Пользователь выходит из вето-рума — очищаем время захода
            elif before.channel and before.channel.id == SATDAT_VOICE_ID and (not after.channel or after.channel.id != SATDAT_VOICE_ID):
                veto_data.veto_join_time = None
                await redis.save(veto_data, veto_key, ttl=timedelta(hours=3))

    @tasks.loop(minutes=1)
    async def veto_check_loop(self):
        async with RedisManager() as redis:
            now_msk = datetime.now(MSK)

            veto_items = await redis.load_many(record_type=SatbatManager, key="veto:*")

            for veto_data in veto_items:
                if not veto_data.veto_join_time:
                    continue

                join_time = datetime.fromisoformat(veto_data.veto_join_time)
                if now_msk - join_time > timedelta(minutes=5):
                    user_id = int(veto_data.user_id)
                    member = None
                    for guild in self.bot.guilds:
                        member = guild.get_member(user_id)
                        if member:
                            break
                    if member and member.voice and member.voice.channel and member.voice.channel.id == SATDAT_VOICE_ID:
                        try:
                            await member.move_to(None)
                        except (disnake.Forbidden, Exception):
                            pass
                    veto_data.veto_join_time = None
                    await redis.save(veto_data, [f"veto:{user_id}"], ttl=timedelta(hours=3))

    @veto_check_loop.before_loop
    async def before_veto_check(self):
        await self.bot.wait_until_ready()
