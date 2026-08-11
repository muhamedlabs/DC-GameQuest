from datetime import datetime, timedelta
import disnake
from disnake import MessageInteraction
from disnake.ext import commands
from .button_id import ButtonID
from BANNED_FILES.config import Embed_Color, ALLOWED_USER_IDS, Community_Image, Greeting_Times
from commands.information_cog.warnings import invalid_input_embed


class GreetingButton(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.processing_users: set[int] = set()
        self.last_click_at: dict[int, datetime] = {}

    @commands.Cog.listener()
    async def on_button_click(self, inter: MessageInteraction):
        custom_id = inter.component.custom_id

        if custom_id.startswith(f"{ButtonID.GREET_USER_PREFIX.value}:"):
            await self.greet_button(inter, custom_id)
            return

    async def greet_button(self, inter: MessageInteraction, custom_id: str):
        if inter.author.id in self.processing_users:
            return

        now = datetime.utcnow()
        last_click = self.last_click_at.get(inter.author.id)
        cooldown = timedelta(seconds=Greeting_Times)
        if last_click is not None and now - last_click < cooldown:
            remaining = round((cooldown - (now - last_click)).total_seconds())
            cooldown_embed = disnake.Embed(
                title="<:danger:1486233459524501644> Канал связи перегружен",
                description=(
                    "> Командный центр **приостановил обработку вашего запроса**. Система зафиксировала **несколько последовательных** обращений к одному лейтенанту за короткий промежуток времени.\n\n"
                    f"Ожидайте **{remaining} секунд**, после чего канал снова будет доступен для передачи радиограммы"
                ),
                color=self.embed_color,
            )
            await inter.response.send_message(embed=cooldown_embed, ephemeral=True)
            return

        self.last_click_at[inter.author.id] = now
        self.processing_users.add(inter.author.id)
        try:
            await inter.response.defer(ephemeral=True, with_message=True)

            admins_mentions = " ".join(f"<@{uid}>" for uid in ALLOWED_USER_IDS)

            try:
                target_id = int(custom_id.split(":", 1)[1])
            except (IndexError, ValueError):
                error_embed = invalid_input_embed(self.embed_color, admins_mentions)
                await inter.edit_original_response(embed=error_embed)
                return

            # Нельзя поздороваться с самим собой
            if inter.author.id == target_id:
                self_embed = disnake.Embed(
                    title="<:danger:1486233459524501644> Защищённая передача отклонена",
                    description=(
                        "> Командный центр **отклонил ваш запрос** после обнаружения **недопустимого адресата** для служебной радиограммы.\n\n"
                        "Действующий протокол военной связи запрещает оператору направлять служебные приветствия на собственный канал связи"
                    ),
                    color=self.embed_color,
                )
                await inter.edit_original_response(embed=self_embed)
                return

            target_user = self.bot.get_user(target_id)
            if target_user is None:
                try:
                    target_user = await self.bot.fetch_user(target_id)
                except disnake.NotFound:
                    not_found_embed = invalid_input_embed(self.embed_color, admins_mentions)
                    await inter.edit_original_response(embed=not_found_embed)
                    return

            # Эмбед для ЛС адресату
            file = disnake.File(Community_Image, filename="community.png")

            dm_embed = disnake.Embed(
                title=f"<:sms:1533371911411732480> Защищённая радиограмма для {target_user.display_name}",
                description=(
                    f"Командный центр установил соединение и доставил **личную передачу** от лейтенанта {inter.author.mention} по защищённому каналу связи.\n\n"
                    "> Передаю привет и желаю успешной службы на сервере Game Quest! "
                    "Пусть каждый день будет наполнен новыми открытиями и интересными событиями!"
                ),
                color=self.embed_color,
            )
            dm_embed.set_image(url="attachment://community.png")
            dm_embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")

            dm_sent = True
            try:
                await target_user.send(embed=dm_embed, file=file)
            except disnake.Forbidden:
                dm_sent = False

            reply_embed = disnake.Embed(
                title=f"<:sms:1533371911411732480> Защищённая радиограмма доставлена для {target_user.display_name}",
                description=( 
                    "> Военная радиостанция **приняла ваш запрос** и выполнила передачу сообщения **по защищённому каналу** оперативной связи.\n\n"
                    f"Командный центр **подтверждает получение радиограммы** что лейтенант {target_user.mention} получил переданное сообщение и находится на связи с системой\n\n"

                ),
                color=self.embed_color,
            )

            if not dm_sent:
                reply_embed = invalid_input_embed(self.embed_color, admins_mentions)

            await inter.edit_original_response(embed=reply_embed)
        finally:
            self.processing_users.discard(inter.author.id)
        