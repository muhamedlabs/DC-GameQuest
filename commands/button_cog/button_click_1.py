import disnake
from disnake import MessageInteraction
from disnake.ext import commands
from .button_id import ButtonID
from BANNED_FILES.config import Embed_Color


class CustomOnButtonClick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.Cog.listener()
    async def on_button_click(self, inter: MessageInteraction):
        button_actions = {
            ButtonID.CHANNEL_CREATION_STATUS.value: self.voice_creation_button,
            ButtonID.CHARTER_AND_CONDUCT.value: self.rules_button
        }
        method = button_actions.get(inter.component.custom_id)
        if method:
            await method(inter)

    async def rules_button(self, inter: MessageInteraction):
        embed = disnake.Embed(
            title="<:book_rules:1395862976174493706> Устав голосового сектора",
            description=(
                "Голосовой сектор — это не просто канал связи, а сердце координации отряда. Здесь звучат команды, строятся планы и рождаются победы. "
                "Каждый участник обязан соблюдать дисциплину и поддерживать боевую атмосферу.\n\n"
                "Уважение к собеседникам — основа любого взаимодействия. Не допускаются крики, фоновые шумы, агрессия или провокации. "
                "Не перебивайте сослуживцев: слушать — значит понимать. Если вам нужно временно отлучиться — активируйте режим тишины.\n\n"
                "Запрещены реклама, самореклама, спам и любые формы деструктивного поведения. В случае возникновения конфликта немедленно обращайтесь к офицерскому составу. "
                "Они обучены быстро реагировать и восстанавливать порядок.\n\n"
                "Пока ты на связи — ты часть команды. Не забывай: дисциплина — это не ограничение, а щит, защищающий нас всех в бою."
            ),
            color=self.embed_color
        )
        await inter.response.send_message(embed=embed, ephemeral=True)

    async def voice_creation_button(self, inter: MessageInteraction):
        embed = disnake.Embed(
            title="<:microphone:1395862990439583854> Доступ к созданию канала",
            description=(
                "В рамках боевой дисциплины установлен лимит — не более **10 активных голосовых частот** в указанной зоне. "
                "Это позволяет сохранить чёткость связи и избежать хаоса в эфире.\n\n"
                "Если все частоты заняты, система временно приостановит возможность создания новых каналов. "
                "В таком случае ты можешь:\n"
                "— Занять позицию в одном из открытых каналов общего доступа;\n"
                "— Либо дождаться, пока один из бойцов покинет частоту.\n\n"
                "Как только связь будет восстановлена и канал освободится — "
                "**возможность создания собственной частоты возобновится автоматически.**\n\n"
                "Помни: порядок в эфире — залог успешной координации всего отряда."
            ),
            color=self.embed_color
        )
        await inter.response.send_message(embed=embed, ephemeral=True)