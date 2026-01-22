import random
import string
import io
import asyncio
import disnake
from datetime import datetime, timedelta
from disnake.ext import commands
from PIL import Image, ImageDraw, ImageFont
from BANNED_FILES.config import Embed_Color

CAPTCHA_TTL = 15  # секунд


class Verification(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.active_captchas: dict[int, dict] = {}

    # ───────────── код ─────────────
    def generate_code(self, length: int = 5) -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    # ───────────── картинка ─────────────
    def generate_captcha_image(self, text: str) -> disnake.File:
        WIDTH, HEIGHT = 280, 110

        BG = (209, 240, 93)     # d1f05d
        NOISE = (43, 43, 43)    # 2B2B2B
        TEXT = (0, 0, 0)       # 000000

        img = Image.new("RGB", (WIDTH, HEIGHT), BG)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arialbd.ttf", 50)
        except Exception:
            font = ImageFont.load_default()

        # шум
        for _ in range(140):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            draw.ellipse((x, y, x + 2, y + 2), fill=NOISE)

        # линии
        for _ in range(3):
            y = random.randint(25, HEIGHT - 25)
            draw.line(
                [(0, y), (WIDTH, y + random.randint(-20, 20))],
                fill=NOISE,
                width=2
            )

        # текст
        spacing = WIDTH // (len(text) + 1)
        for i, char in enumerate(text):
            char_img = Image.new("RGBA", (60, 70), (0, 0, 0, 0))
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((10, 10), char, font=font, fill=TEXT)

            angle = random.randint(-25, 25)
            char_img = char_img.rotate(angle, expand=1)

            img.paste(
                char_img,
                (spacing * (i + 1) - 20, random.randint(25, 40)),
                char_img
            )

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return disnake.File(buffer, filename="captcha.png")

    # ───────────── авто-очистка ─────────────
    async def expire_captcha(self, user_id: int):
        await asyncio.sleep(CAPTCHA_TTL)
        self.active_captchas.pop(user_id, None)

    # ───────────── команда ─────────────
    @commands.slash_command(
        name="verify",
        description="Верификация от ботов"
    )
    async def verify(
        self,
        inter: disnake.ApplicationCommandInteraction,
        code: str = commands.Param(
            default=None,
            description="Код с картинки"
        ),
    ):
        if inter.author.bot:
            return

        await inter.response.defer(ephemeral=True)

        user_id = inter.author.id
        now = datetime.utcnow()

        # ─── первый вызов ───
        if code is None:
            captcha_code = self.generate_code()
            image = self.generate_captcha_image(captcha_code)

            self.active_captchas[user_id] = {
                "code": captcha_code,
                "expires": now + timedelta(seconds=CAPTCHA_TTL),
            }

            self.bot.loop.create_task(self.expire_captcha(user_id))

            embed = disnake.Embed(
                title="🛡 Анти-бот верификация",
                description=(
                    "Введите код с картинки:\n"
                    "`/verify КОД`\n\n"
                    "⏱ **Время действия:** 15 секунд"
                ),
                color=self.embed_color
            )
            embed.set_image(url="attachment://captcha.png")

            await inter.edit_original_response(
                embed=embed,
                file=image
            )
            return

        # ─── проверка ───
        data = self.active_captchas.get(user_id)

        if not data:
            await inter.edit_original_response(
                content="❌ Капча не найдена или истекло время.\nИспользуй `/verify` ещё раз."
            )
            return

        if now > data["expires"]:
            self.active_captchas.pop(user_id, None)
            await inter.edit_original_response(
                content="⏱ Время истекло. Вызови `/verify` заново."
            )
            return

        if code.upper() != data["code"]:
            await inter.edit_original_response(
                content="❌ Неверный код. Попробуй ещё раз."
            )
            return

        # ─── успех ───
        self.active_captchas.pop(user_id, None)

        await inter.edit_original_response(
            content="✅ **Успешно верифицирован!**"
        )
