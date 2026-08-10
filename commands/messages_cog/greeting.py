import disnake
from disnake.ext import commands
from BANNED_FILES.config import CHAT_CHANNEL_ID, Embed_Color, Community_Image, Words_Greetings


class GreetingResponder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.greetings = Words_Greetings
        self.channel_id = CHAT_CHANNEL_ID
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return

        content_lower = message.content.lower()
        if any(content_lower.startswith(greet) for greet in self.greetings):
            member = message.guild.get_member(message.author.id) if message.guild else None
            mention_text = member.mention if member else message.author.mention

            embed = disnake.Embed(
                title=f"<:aiac:1390972515295170600> Здравия желаю лейтенант {message.author.display_name}",
                description=(
                    f"> Мы рады видеть **вас** {mention_text} здесь и надеемся, что ваше время **пребывания** будет приятным и наполненным позитивом.\n\n"
                    "Если у вас возникнут вопросы или потребуется **помощь**, не стесняйтесь **обращаться** "
                    "к администраторам или модераторам через бота.\n\n"
                    "<:security:1522868634941390960> Также, пожалуйста, придерживайтесь правил сервера: <#1195867893594869853>"
                ),
                color=self.embed_color
            )

            file = disnake.File(Community_Image, filename="community.png")
            embed.set_image(url="attachment://community.png")
            embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

            if isinstance(message.channel, disnake.DMChannel):
                await message.channel.send(embed=embed, file=file)
            elif message.channel.id == self.channel_id and member is not None:
                await message.channel.send(
                    embed=embed,
                    file=file,
                    flags=disnake.MessageFlags(suppress_notifications=True)
                )
