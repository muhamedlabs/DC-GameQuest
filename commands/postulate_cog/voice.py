import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
import pytz
import asyncio
from commands.button_cog.button_id import ButtonID
from BANNED_FILES.config import Embed_Color, LATENT_TOWER_IDS, CREATE_PRIVATE_ID, Voice_Image, RedisManager
from redis_storage.postulate_message import Postulate_Message

REDIS_KEY_PREFIX = "auto_voice_message"
MOSCOW_TZ = pytz.timezone("Europe/Moscow")


class AutoVoiceInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.redis = RedisManager()

    async def cog_load(self):
        await self.redis.__aenter__()
        await self.restore_views()
        self.message_rotation_loop.start()

    def cog_unload(self):
        self.message_rotation_loop.cancel()
        asyncio.create_task(self.redis.__aexit__(None, None, None))

    def create_embed_and_file(self, guild_name: str):
        role_mentions = " ".join(f"<@&{role_id}>" for role_id in LATENT_TOWER_IDS)
        embed = disnake.Embed(
            title=f"<:radarvoice:1395799324083884214> АВТОГОЛОСОВОЙ СЕКТОР - {guild_name.upper()}",
            description=(
                f"> Зайдите в командный пункт — <#{CREATE_PRIVATE_ID}>. "
                f"После этого система автоматически перебросит тебя на закреплённую за тобой боевую частоту связи.\n\n"
                f"<:subtitle:1395816518507429990> **ПОЛНОМОЧИЯ ЛЕЙТЕНАНТА:**\n"
                f"Перемещать, мутить и отключать звук у участников, а также создавать приглашения для друзей и контролировать порядок в канале при необходимости.\n\n"
                f"<:subtitle:1395816518507429990> **СВОБОДНЫЙ ПРОПУСК БЕЗ ВЫЗОВА:**\n"
                f"В сектор допускаются только лейтенанты, обладающие следующие звания: {role_mentions}.\n\n"
                f"<:warning2:1395814941520302191> **КОМАНДНОЕ СООБЩЕНИЕ:**\n"
                f"Изменение названия подразделения и ограничение численности личного состава требуют активированной двухфакторной аутентификации (2FA) на вашем боевом аккаунте."
            ),
            color=self.embed_color
        )
        embed.set_image(url=f"attachment://{Voice_Image.split('/')[-1]}")
        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
        file = disnake.File(Voice_Image, filename=Voice_Image.split('/')[-1])
        return embed, file

    async def restore_views(self):
        prefix = f"{REDIS_KEY_PREFIX}:*"
        records = await self.redis.load_many(Postulate_Message, prefix)
        for record in records:
            try:
                channel = self.bot.get_channel(int(record.channel_id))
                if not channel:
                    continue
                await self.bot.add_view(
                    VoiceInfoView(self.embed_color),
                    message_id=int(record.message_id)
                )
            except Exception as e:
                print(f"Не удалось восстановить View для {record.channel_id}: {e}")

    @commands.command(name="автовойс", help="Показать инструкцию по автоголосовым каналам")
    async def voice_info(self, ctx: commands.Context):
        guild_name = ctx.guild.name if ctx.guild else "Неизвестный сервер"
        embed, file = self.create_embed_and_file(guild_name)
        view = VoiceInfoView(self.embed_color)
        message = await ctx.send(embed=embed, file=file, view=view)

        now_msk = datetime.now(tz=MOSCOW_TZ)
        record = Postulate_Message(
            channel_id=str(ctx.channel.id),
            message_id=str(message.id),
            time_message=now_msk.isoformat()
        )
        key = f"{REDIS_KEY_PREFIX}:{ctx.channel.id}"
        await self.redis.save(record, key)

    @tasks.loop(hours=24)
    async def message_rotation_loop(self):
        prefix = f"{REDIS_KEY_PREFIX}:*"
        records = await self.redis.load_many(Postulate_Message, prefix)
        if not records:
            return

        now_msk = datetime.now(tz=MOSCOW_TZ)
        for record in records:
            try:
                sent_time = datetime.fromisoformat(record.time_message)
                sent_time = sent_time.astimezone(MOSCOW_TZ)

                if now_msk - sent_time >= timedelta(days=90):
                    channel = self.bot.get_channel(int(record.channel_id))
                    if not channel:
                        continue
                    try:
                        old_message = await channel.fetch_message(int(record.message_id))
                        await old_message.delete()
                    except disnake.NotFound:
                        pass

                    guild_name = channel.guild.name if channel.guild else "Неизвестный сервер"
                    embed, file = self.create_embed_and_file(guild_name)
                    view = VoiceInfoView(self.embed_color)
                    new_message = await channel.send(embed=embed, file=file, view=view)

                    updated_record = Postulate_Message(
                        channel_id=str(channel.id),
                        message_id=str(new_message.id),
                        time_message=now_msk.isoformat()
                    )
                    key = f"{REDIS_KEY_PREFIX}:{channel.id}"
                    await self.redis.save(updated_record, key)

            except Exception as e:
                print(f"Ошибка при обновлении сообщения в {record.channel_id}: {e}")


class VoiceInfoView(disnake.ui.View):
    def __init__(self, embed_color: disnake.Color):
        super().__init__(timeout=None)
        self.embed_color = embed_color

        # Кнопки с нужными custom_id
        self.add_item(disnake.ui.Button(
            label="Устав и поведение",
            style=disnake.ButtonStyle.success,
            emoji=disnake.PartialEmoji(name="book_rules2", id=1395862918423117854),
            custom_id=ButtonID.CHARTER_AND_CONDUCT.value
        ))
        self.add_item(disnake.ui.Button(
            label="Статус создания канала",
            style=disnake.ButtonStyle.success,
            emoji=disnake.PartialEmoji(name="microphone2", id=1395862933237399692),
            custom_id=ButtonID.CHANNEL_CREATION_STATUS.value
        ))
