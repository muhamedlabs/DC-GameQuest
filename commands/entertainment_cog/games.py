import disnake
from disnake.ext import commands
from disnake import ApplicationCommandInteraction
from BANNED_FILES.config import Embed_Color, Pieces_Gif

class GameOrders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(name="симуляции", description="Центр подготовки веб-бойцов")
    async def game_order(self, inter: ApplicationCommandInteraction):
        embed = disnake.Embed(
            title="<:award:1401626933346959410> Портал боевой подготовки",
            description=(
                "> **Лейтенант**, штаб активировал для тебя **доступ** к полигону цифровых операций. Здесь проходят **тренировки** всех подразделений"
            ),
            color=self.embed_color
        )

        embed.add_field(
            name="<:keyboardopen:1401634582599565366> Стратегический маршрут:",
            value="[Вход в симуляционный веб-центр](https://muhamedlabs.pro/sembly/home)",
            inline=False
        )

        file = disnake.File(Pieces_Gif, filename="arcade.gif")
        embed.set_image(url="attachment://arcade.gif")

        await inter.response.send_message(embed=embed, file=file)

