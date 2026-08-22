import os
import random
import string
import io
import asyncio
import math
from datetime import datetime, timedelta

import disnake
from disnake.ext import commands, tasks
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from ashredis import MISSING

from BANNED_FILES.config import Embed_Color, Captcha_Times, Verification_Valid, VERIFICATION_ID, Community_Image, Font_Preview, RedisManager
from redis_storage.verification_captcha import VerificationCaptcha
from commands.information_cog.time import hours_time


class Verification(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.active_captchas: dict[int, dict] = {}

        self.BG    = (209, 240, 93)
        self.TEXT  = (0, 0, 0)
        self.NOISE = (43, 43, 43)

        self.FOOTER = "Благодарим за проявленный интерес к нашему спецпроекту!"

        self.VISIBILITY = {
            "challenge":        True,   # картинка с капчей
            "already_verified": True,   # у пользователя уже есть роль
            "not_found":        True,   # капча не найдена / истекла
            "expired":          True,   # истекло время
            "wrong_code":       True,   # неверный код
            "success":          False,  # успешная верификация
        }

    async def cog_load(self):
        self.check_expired_verifications.start()

    def cog_unload(self):
        self.check_expired_verifications.cancel()

    def generate_code(self, length: int = 5) -> str:
        chars = "АБВГДЕЖКЛМНПРСТУФХЦЧШЭЮЯ23456789"
        return "".join(random.choices(chars, k=length))

    def community_file(self) -> disnake.File:
        return disnake.File(Community_Image, filename="community.png")

    def generate_captcha_image(self, text: str) -> disnake.File:
        WIDTH, HEIGHT = 885, 331

        scale = WIDTH / 320

        BG    = self.BG
        TEXT  = self.TEXT
        NOISE = self.NOISE

        img  = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        # фоновая сетка
        grid_step = max(1, int(18 * scale))
        for x in range(0, WIDTH, grid_step):
            draw.line([(x, 0), (x, HEIGHT)], fill=NOISE, width=1)
        for y in range(0, HEIGHT, grid_step):
            draw.line([(0, y), (WIDTH, y)], fill=NOISE, width=1)

        # случайные точки шума
        for _ in range(int(300 * scale)):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            r = random.randint(1, max(1, int(3 * scale)))
            color = (
                min(255, NOISE[0] + random.randint(-20, 20)),
                min(255, NOISE[1] + random.randint(-20, 20)),
                min(255, NOISE[2] + random.randint(-20, 20)),
            )
            draw.ellipse((x - r, y - r, x + r, y + r), fill=color)

        # синусоидальные линии помехи
        for _ in range(4):
            amplitude = random.randint(int(6 * scale), int(18 * scale))
            frequency = random.uniform(0.03, 0.07) / scale
            phase     = random.uniform(0, math.pi * 2)
            y_base    = random.randint(int(20 * scale), HEIGHT - int(20 * scale))
            line_w    = max(1, int(2 * scale))
            points    = []
            for x in range(0, WIDTH, 3):
                y = int(y_base + amplitude * math.sin(frequency * x + phase))
                points.append((x, y))
            for i in range(len(points) - 1):
                draw.line([points[i], points[i + 1]], fill=NOISE, width=line_w)

        # загрузка шрифта
        font_size = int(52 * scale)
        try:
            font = ImageFont.truetype(Font_Preview, font_size)
        except Exception as e:
            print(f"Не удалось загрузить шрифт {Font_Preview}: {e}")
            font = ImageFont.load_default()

        # рендер каждого символа с трансформациями
        char_box_w = int(70 * scale)
        char_box_h = int(80 * scale)
        char_width = WIDTH // (len(text) + 1)
        for i, char in enumerate(text):
            char_img  = Image.new("RGBA", (char_box_w, char_box_h), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)

            # тень для объёма
            shadow_offset = int(12 * scale)
            base_offset   = int(10 * scale)
            shadow_color  = (80, 80, 80, 180)
            char_draw.text((shadow_offset, shadow_offset), char, font=font, fill=shadow_color)
            char_draw.text((base_offset, base_offset), char, font=font, fill=TEXT + (255,))

            # случайный поворот и масштаб
            angle    = random.randint(-30, 30)
            rand_scale = random.uniform(0.85, 1.15)
            new_size = (int(char_box_w * rand_scale), int(char_box_h * rand_scale))
            char_img = char_img.resize(new_size, Image.LANCZOS)
            char_img = char_img.rotate(angle, expand=True)

            x = char_width * (i + 1) - int(25 * scale) + random.randint(int(-5 * scale), int(5 * scale))
            y = random.randint(int(15 * scale), int(35 * scale))
            img.paste(char_img, (x, y), char_img)

        # лёгкий блюр для склейки
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6 * scale))

        # виньетка по краям
        vignette = Image.new("RGB", (WIDTH, HEIGHT), (180, 210, 70))
        v_draw   = ImageDraw.Draw(vignette)
        v_steps  = int(30 * scale)
        for step in range(v_steps):
            opacity = int(120 * (1 - step / v_steps))
            color   = (
                max(0, BG[0] - opacity // 2),
                max(0, BG[1] - opacity // 2),
                max(0, BG[2] - opacity // 3),
            )
            v_draw.rectangle([step, step, WIDTH - step, HEIGHT - step], outline=color)
        img = Image.blend(img, vignette, alpha=0.12)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return disnake.File(buffer, filename="captcha.png")

    def error_embed(self, description: str) -> disnake.Embed:
        embed = disnake.Embed(
            title="<:lockslash:1528278437502914570> Контрольно-пропускной пункт не пройден",
            description=description,
            color=self.embed_color
        )
        embed.set_image(url="attachment://community.png")
        embed.set_footer(text=self.FOOTER)
        return embed

    def success_embed(self, member: disnake.Member) -> disnake.Embed:
        embed = disnake.Embed(
            title="<:unlock:1528278439600066680> Контрольно-пропускной пункт пройден",
            description=(
                f"> Лейтенант {member.mention}, идентификация завершена. Все системы **подтвердили** вашу "
                f"**личность**.\n\nДоступ к охраняемой территории открыт. Желаем **успешной службы**"
            ),
            color=self.embed_color
        )
        embed.set_image(url="attachment://community.png")
        embed.set_footer(text=self.FOOTER)
        return embed

    def already_verified_embed(self, member: disnake.Member) -> disnake.Embed:
        embed = disnake.Embed(
            title="<:unlock:1528278439600066680> Контрольно пункт уже выдал вам допуск",
            description=(
                f"> Лейтенант {member.mention}, военная система безопасности уже **завершила** проверку вашей "
                f"личности.\n\nДопуск на территорию базы был успешно выдан ранее, поэтому повторное "
                f"прохождение **верификации** не требуется"
            ),
            color=self.embed_color
        )
        embed.set_image(url="attachment://community.png")
        embed.set_footer(text=self.FOOTER)
        return embed

    async def expire_captcha(self, user_id: int):
        await asyncio.sleep(Captcha_Times)
        self.active_captchas.pop(user_id, None)

    # ── Работа с Redis-записью верификации ──────────────────────────────────
    async def get_existing_record(self, user_id: int) -> VerificationCaptcha | None:
        """Получает существующую запись пользователя из Redis"""
        try:
            async with RedisManager() as redis:
                record = await redis.load(VerificationCaptcha, key=f"{user_id}")
                return record
        except Exception as e:
            print(f"Ошибка получения записи из Redis: {e}")
            return None

    async def save_verification_record(self, member: disnake.Member):
        try:
            # Получаем существующую запись, чтобы сохранить time_message
            existing = await self.get_existing_record(member.id)
            
            # Создаем новую запись с обновленными данными
            record = VerificationCaptcha(
                user_id=str(member.id),
                username=member.name,
                content="Прошёл верификацию",
                time_captcha=hours_time,
                time_message=existing.time_message if existing and existing.time_message else MISSING
            )
            
            async with RedisManager() as redis:
                await redis.save(record, key=f"{member.id}")
        except Exception as e:
            print(f"ОШИБКА сохранения в Redis: {e}")

    async def _expire_verification(self, record: VerificationCaptcha):
        """Снимает роль верификации у пользователя и помечает запись как неактуальную."""
        user_id = int(record.user_id)

        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member is None:
                continue
            role = guild.get_role(VERIFICATION_ID)
            if role is not None and role in member.roles:
                try:
                    await member.remove_roles(role, reason="Истёк срок действия верификации")
                except disnake.Forbidden:
                    print(f"Нет прав снять роль верификации у {member.name}")

        record.content = "Верификация не пройдена"
        async with RedisManager() as redis:
            await redis.save(record, key=record.user_id)

    @tasks.loop(hours=24)
    async def check_expired_verifications(self):
        try:
            async with RedisManager() as redis:
                records = await redis.load_many(VerificationCaptcha, "*")

            for record in records:
                if record.content != "Прошёл верификацию":
                    continue

                # Парсим время из строки (формат hours_time: "дд.мм.гггг чч:мм:сс")
                try:
                    time_dt = datetime.strptime(record.time_captcha, "%d.%m.%Y %H:%M:%S")
                    now_dt = datetime.strptime(hours_time, "%d.%m.%Y %H:%M:%S")
                except Exception as e:
                    print(f"Ошибка парсинга времени {record.time_captcha}: {e}")
                    continue

                if now_dt - time_dt >= timedelta(days=Verification_Valid):
                    await self._expire_verification(record)
        
        except Exception as e:
            print(f"ОШИБКА в check_expired_verifications: {e}")

    @check_expired_verifications.before_loop
    async def before_check_expired_verifications(self):
        await self.bot.wait_until_ready()

    @commands.slash_command(name="идентификация",description="Военная система антиботовой защиты")

    async def verify(
        self,
        inter: disnake.ApplicationCommandInteraction,
        code: str = commands.Param(default=None, name="код", description="Введите код, отображённый на изображении"),

    ):
        if inter.author.bot:
            return

        user_id = inter.author.id
        now     = datetime.utcnow()

        # Получаем участника и сервер для верификации
        guild = inter.guild
        member = inter.author

        if guild is None:
            for bot_guild in self.bot.guilds:
                found_member = bot_guild.get_member(user_id)

                if found_member is not None:
                    guild = bot_guild
                    member = found_member
                    break

        already_has_role = False
        if guild is not None:
            role = guild.get_role(VERIFICATION_ID)
            if role is not None and role in member.roles:
                already_has_role = True

        if code is None and already_has_role:
            scenario = "already_verified"
        elif code is None:
            scenario = "challenge"
        else:
            data = self.active_captchas.get(user_id)
            if not data:
                scenario = "not_found"
            elif now > data["expires"]:
                scenario = "expired"
            elif code.upper() != data["code"]:
                scenario = "wrong_code"
            else:
                scenario = "success"

        await inter.response.defer(ephemeral=self.VISIBILITY[scenario])

        if scenario == "already_verified":
            await inter.edit_original_response(
                embed=self.already_verified_embed(member),
                file=self.community_file()
            )
            return

        if scenario == "challenge":
            captcha_code = self.generate_code()
            image        = self.generate_captcha_image(captcha_code)

            self.active_captchas[user_id] = {
                "code":    captcha_code,
                "expires": now + timedelta(seconds=Captcha_Times),
            }

            self.bot.loop.create_task(self.expire_captcha(user_id))

            embed = disnake.Embed(
                title="<:lock:1528278435913535488> Контрольно-пропускной пункт",
                description=(
                    f"Для получения допуска введи **код с планшета разведки**, используя команду: "
                    f"`/идентификация XXXXX`\n\n"
                    f"**Пропуск действителен:** 2 минуты"
                ),
                color=self.embed_color
            )
            embed.set_footer(text=self.FOOTER)
            embed.set_image(url="attachment://captcha.png")

            await inter.edit_original_response(embed=embed, file=image)
            return

        if scenario == "not_found":
            await inter.edit_original_response(
                embed=self.error_embed(
                    "> Лейтенант, запись о вашем допуске **не найдена** в системе безопасности, либо срок "
                    "действия пропуска истёк.\n\nДля восстановления доступа необходимо заново "
                    "**подтвердить** личность"
                ),
                file=self.community_file()
            )
            return

        if scenario == "expired":
            self.active_captchas.pop(user_id, None)
            await inter.edit_original_response(
                embed=self.error_embed(
                    "> Лейтенант, система безопасности зафиксировала **окончание** срока действия пропуска.\n\n"
                    "Для восстановления доступа **требуется** повторная идентификация"
                ),
                file=self.community_file()
            )
            return

        if scenario == "wrong_code":
            await inter.edit_original_response(
                embed=self.error_embed(
                    "> Лейтенант, код доступа не прошёл проверку контрольно-пропускного пункта.\n\nПопытка "
                    "**идентификации** завершилась неудачей. Проверьте полученный код и повторите "
                    "**процедуру** верификации"
                ),
                file=self.community_file()
            )
            return

        # scenario == "success"
        self.active_captchas.pop(user_id, None)

        role = guild.get_role(VERIFICATION_ID) if guild else None
        if role is not None:
            try:
                await member.add_roles(role, reason="Успешная анти-бот верификация")
            except disnake.Forbidden:
                print(f"Нет прав выдать роль {member.name}")
        else:
            print(f"Роль VERIFICATION_ID ({VERIFICATION_ID}) не найдена на сервере")

        await self.save_verification_record(member)

        await inter.edit_original_response(
            embed=self.success_embed(member),
            file=self.community_file()
        )