import os
import zipfile
import tempfile
import asyncio
import disnake
from disnake.ext import commands
from BANNED_FILES.config import ADS_CODES, POPPY_FOLDER, ALLOWED_USER_IDS

class AdsCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def delete_after_delay(self, message, delay=180):
        await asyncio.sleep(delay)
        try:
            await message.delete()
        except:
            pass

    @commands.command(name="Ads", help="Передача засекреченной документации")

    async def send_ads(self, ctx: commands.Context, code: str):
        # Ограничение по ID пользователя
        if ctx.author.id not in ALLOWED_USER_IDS:
            return  # Молча игнорируем

        if code not in ADS_CODES:
            return  # Код не найден — игнорируем

        targets = ADS_CODES[code]

        # Унифицируем в список
        if isinstance(targets, str):
            targets = [targets]

        paths = [os.path.join(POPPY_FOLDER, t) for t in targets]

        # Пропускаем, если отсутствует хотя бы один файл/папка
        if not all(os.path.exists(p) for p in paths):
            return

        # Если один файл — отправляем напрямую
        if len(paths) == 1 and os.path.isfile(paths[0]):
            msg = await ctx.send(file=disnake.File(paths[0]))
            asyncio.create_task(self.delete_after_delay(msg))
            print(f"File #{code} sent to Discord channel {ctx.channel.id}")
            return

        # Создание архива
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            zip_path = tmp.name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for path in paths:
                if os.path.isfile(path):
                    zipf.write(path, os.path.basename(path))
                elif os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for file in files:
                            full_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_path, start=path)
                            zipf.write(full_path, arcname)

        msg = await ctx.send(file=disnake.File(zip_path, filename="BANNED_FILES.zip"))
        asyncio.create_task(self.delete_after_delay(msg))
        os.remove(zip_path)
        print(f"Archive #{code} sent to Discord channel {ctx.channel.id}")
