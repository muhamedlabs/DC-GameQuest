import disnake
from disnake.ext import commands
from disnake import ApplicationCommandInteraction
import aiohttp
import os
from BANNED_FILES.config import Interpreter_Gif, Embed_Color, deepl_developer

DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"

LANG_CODES = {
    "Русский": "RU",
    "Английский": "EN",
    "Украинский": "UK"
}

class Translator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(name="интерпретация", description="Дешифровка перехваченного сообщения")
    async def translate(
        self,
        inter: ApplicationCommandInteraction,
        text: str = commands.Param(name="текст", description="Перехваченный фрагмент для перевода"),
        язык: str = commands.Param(
            name="язык",
            choices=list(LANG_CODES.keys()),
            description="Язык, на который необходимо выполнить дешифровку"
        )
    ):
        await inter.response.defer()

        lang_code = LANG_CODES[язык]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                DEEPL_API_URL,
                data={
                    "auth_key": deepl_developer,
                    "text": text,
                    "target_lang": lang_code
                }
            ) as response:
                result = await response.json()

        if "translations" not in result:
            await inter.edit_original_response("Не удалось установить связь с дешифровочным центром")
            return

        translated_text = result["translations"][0]["text"]

        embed = disnake.Embed(
            title="<:languagesquare:1401982335624155208> Узел расшифровки сообщений",
            description=(
                f"> Шифровка **успешно** обработана. Перевод направлен в штаб. Использован **протокол** дешифровки — `{язык.upper()}`"
            ),
            color=self.embed_color
        )

        embed.add_field(name="<:messageminus:1401982354138071072> Исходное сообщение:", value=f"```{text}```", inline=False)
        embed.add_field(name="<:messageedit:1401982365097656411> Результат декодирования:", value=f"```{translated_text}```", inline=False)

        file = disnake.File(Interpreter_Gif, filename=os.path.basename(Interpreter_Gif))
        embed.set_image(url=f"attachment://{os.path.basename(Interpreter_Gif)}")

        await inter.edit_original_response(embed=embed, file=file)
