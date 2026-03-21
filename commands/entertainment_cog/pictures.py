import aiohttp
import disnake
from disnake.ext import commands
from BANNED_FILES.config import Embed_Color, unsplash_developer


class Unsplash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

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

        url = f"https://api.unsplash.com/photos/random?query={query}&client_id={unsplash_developer}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await inter.edit_original_message(
                        "Сбой связи с разведсервисом. Данные недоступны."
                    )
                    return

                data = await resp.json()

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

        await inter.edit_original_message(embed=embed)
