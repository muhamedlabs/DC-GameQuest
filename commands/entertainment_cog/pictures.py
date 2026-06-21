import aiohttp
import disnake
from disnake.ext import commands
from BANNED_FILES.config import Embed_Color, unsplash_developer, deepl_developer

DEEPL_API_URL = "https://api-free.deepl.com/v2/translate"


class Unsplash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    async def translate_to_english(self, session: aiohttp.ClientSession, text: str) -> str:
        """Переводит запрос на английский для лучшего поиска на Unsplash."""
        try:
            async with session.post(
                DEEPL_API_URL,
                headers={"Authorization": f"DeepL-Auth-Key {deepl_developer}"},
                data={"text": text, "target_lang": "EN"}
            ) as resp:
                if resp.status != 200:
                    return text  # если перевод не удался — используем оригинал

                result = await resp.json()
                translations = result.get("translations")
                if translations:
                    return translations[0]["text"]
                return text

        except Exception:
            return text  # при любой ошибке — fallback на оригинальный запрос

    @commands.slash_command(
        name="разведданные",
        description="Визуальные данные с разведсервиса Unsplash"
    )
    async def unsplash_image(
        self,
        inter: disnake.ApplicationCommandInteraction,
        query: str = commands.Param(
            name="запрос",
            description="Ключевое слово или объект разведки (напр: танк, дрон, база, ночь)"
        )
    ):
        await inter.response.defer()

        try:
            async with aiohttp.ClientSession() as session:
                search_query = await self.translate_to_english(session, query)

                url = (
                    "https://api.unsplash.com/photos/random"
                    f"?query={search_query}&client_id={unsplash_developer}"
                )

                async with session.get(url) as resp:
                    if resp.status != 200:
                        await inter.edit_original_response(
                            content="Сбой связи с разведсервисом. Данные недоступны."
                        )
                        return

                    data = await resp.json()

        except Exception as e:
            await inter.edit_original_response(
                content=f"Сбой соединения с разведсервисом.\n```{e}```"
            )
            return

        if not data or "urls" not in data:
            await inter.edit_original_response(
                content="Разведсервис вернул некорректные данные."
            )
            return

        image_url = data["urls"]["regular"]
        author_name = data["user"]["name"]
        author_username = data["user"]["username"]
        author_profile = f"https://unsplash.com/@{author_username}"

        description = data.get("description") or data.get("alt_description") or "Описание отсутствует"

        embed = disnake.Embed(
            title="<:camera:1400124899120382003> Фотоматериалы с базы Unsplash",
            description=(
                f"> Кадры, которые **работают** на тебя. Быстро. Точно. Свободно!\n\n"
                f"<:usersquar:1388889541645172957> **Поставщик данных:** [{author_name}]({author_profile})\n"
                f"<:subtitle:1395816518507429990> **Данные с командного пункта:**\n```{description}```"
            ),
            color=self.embed_color
        )
        embed.set_image(url=image_url)

        await inter.edit_original_response(embed=embed)