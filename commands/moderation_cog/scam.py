import asyncio
from datetime import datetime, timedelta

import disnake
from disnake.ext import commands

from BANNED_FILES.config import VERIFICATION_ID, ALLOWED_USER_IDS, Embed_Color, Community_Image, RedisManager
from redis_storage.verification_captcha import VerificationCaptcha
from commands.information_cog.time import hours_time


class ScamVerification(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.FOOTER = "Благодарим за проявленный интерес к нашему спецпроекту!"
        self.verification_role_id = VERIFICATION_ID
        self.allowed_users = set(ALLOWED_USER_IDS)

    async def cog_load(self):
        pass

    def cog_unload(self):
        pass

    def should_ignore(self, user: disnake.Member) -> bool:
        if user.bot:
            return True
        if user.id in self.allowed_users:
            return True
        return False
    
    def community_file(self) -> disnake.File:
        return disnake.File(Community_Image, filename="community.png")

    def has_verification_role(self, member: disnake.Member) -> bool:
        if not member.guild:
            return False
        role = member.guild.get_role(self.verification_role_id)
        if role is None:
            return False
        return role in member.roles

    async def get_user_verification_record(self, user_id: int) -> VerificationCaptcha | None:
        """Получает запись пользователя из Redis"""
        try:
            async with RedisManager() as redis:
                record = await redis.load(VerificationCaptcha, key=f"{user_id}")
                return record
        except Exception as e:
            print(f"Ошибка получения записи из Redis для {user_id}: {e}")
            return None

    async def save_user_verification_record(self, user_id: int, username: str, time_message: str):
        """Сохраняет запись пользователя в Redis"""
        try:
            existing = await self.get_user_verification_record(user_id)
            
            if existing:
                existing.time_message = time_message
                record = existing
            else:
                record = VerificationCaptcha(
                    user_id=str(user_id),
                    username=username,
                    content="Ожидает верификации",
                    time_captcha="Ожидает...",
                    time_message=time_message
                )
            
            async with RedisManager() as redis:
                await redis.save(record, key=f"{user_id}")
        except Exception as e:
            print(f"Ошибка сохранения в Redis для {user_id}: {e}")

    async def should_send_warning(self, member: disnake.Member) -> bool:
        """Проверяет, можно ли отправить предупреждение (прошло 3+ часа)"""
        record = await self.get_user_verification_record(member.id)
        if record and record.time_message:
            try:
                last_time = datetime.strptime(record.time_message, "%d.%m.%Y %H:%M:%S")
                current_time = datetime.strptime(hours_time, "%d.%m.%Y %H:%M:%S")
                time_diff = current_time - last_time
                
                if time_diff < timedelta(hours=3):
                    return False
            except Exception as e:
                print(f"Ошибка парсинга времени для {member.name}: {e}")
        return True

    async def send_warning(self, member: disnake.Member, action: str):
        """Отправляет предупреждение в ЛС и сохраняет время в Redis"""
        try:
            embed = disnake.Embed(
                title="<:lock:1528278435913535488> Требуется пройти контрольно пункт",
                description=(
                    f"> **Лейтенант** {member.mention} попытался {action}, однако его личность ещё **не подтверждена** системой безопасности.\n\n"
                    "Для получения допуска необходимо пройти верификацию с помощью команды: `/идентификация`\n\n"
                    "До завершения процедуры **ваши** сообщения будут **удаляться**, а вход в голосовые каналы **блокироваться**"
                ),
                color=self.embed_color
            )

            embed.set_image(url="attachment://community.png")
            embed.set_footer(text=self.FOOTER)
            
            await member.send(embed=embed, file=self.community_file())
            
            current_time = hours_time
            await self.save_user_verification_record(member.id, member.name, current_time)
            
        except Exception as e:
            print(f"Не удалось отправить ЛС {member.name}: {e}")

    async def warn_after_delay(self, member: disnake.Member, action: str):
        """Отправляет предупреждение через 5 минут, если прошло больше 3 часов с последнего"""
        try:
            await asyncio.sleep(300)  # 5 минут
            
            if self.has_verification_role(member):
                return
            
            if self.should_ignore(member):
                return
            
            if not await self.should_send_warning(member):
                return
            
            await self.send_warning(member, action)
            
        except Exception as e:
            print(f"Ошибка в warn_after_delay для {member.name}: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.guild is None:
            return
            
        if message.author.bot:
            return
        if message.author.id == self.bot.user.id:
            return
        if self.should_ignore(message.author):
            return
        if self.has_verification_role(message.author):
            return
        
        try:
            await message.delete()
            self.bot.loop.create_task(self.warn_after_delay(message.author, "написать сообщение"))
        except Exception as e:
            print(f"Ошибка удаления сообщения от {message.author.name}: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: disnake.Member, before: disnake.VoiceState, after: disnake.VoiceState):
        if member.bot:
            return
        if after.channel is None:
            return
        if self.should_ignore(member):
            return
        if self.has_verification_role(member):
            return
        
        # Проверяем, можно ли отправлять предупреждение (прошло 3+ часа)
        if not await self.should_send_warning(member):
            # Если предупреждение уже было недавно - просто выгоняем и удаляем сообщения
            try:
                await member.move_to(None)
                if after.channel:
                    async for message in after.channel.history(limit=10):
                        if message.author.id == member.id:
                            try:
                                await message.delete()
                            except:
                                pass
                return
            except:
                return
        
        try:
            # Выгоняем из войса
            await member.move_to(None)
            
            # Удаляем сообщения пользователя в голосовых каналах за последние 10 сообщений
            if after.channel:
                async for message in after.channel.history(limit=10):
                    if message.author.id == member.id:
                        try:
                            await message.delete()
                        except Exception as e:
                            print(f"Ошибка удаления голосового сообщения: {e}")
            
            # Запускаем таймер на отправку предупреждения
            self.bot.loop.create_task(self.warn_after_delay(member, "зайти в голосовой канал"))
        except Exception as e:
            print(f"Ошибка выгона из войса {member.name}: {e}")