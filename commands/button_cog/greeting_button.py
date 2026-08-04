import disnake
from disnake import MessageInteraction
from disnake.ext import commands
from .button_id import ButtonID
from BANNED_FILES.config import Embed_Color, ALLOWED_USER_IDS, Community_Image
from commands.information_cog.warnings import invalid_input_embed


class GreetingButton(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.Cog.listener()
    async def on_button_click(self, inter: MessageInteraction):
        custom_id = inter.component.custom_id

        if custom_id.startswith(f"{ButtonID.GREET_USER_PREFIX.value}:"):
            await self.greet_button(inter, custom_id)
            return

    async def greet_button(self, inter: MessageInteraction, custom_id: str):
        # with_message=True — обязателен для компонентных interaction'ов,
        # иначе defer() тихо апдейтит ИСХОДНОЕ сообщение (с IS_COMPONENTS_V2),
        # и потом edit_original_response с embed падает с ошибкой.
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
                    "Командный центр **отклонил запрос**. Операция не соответствует установленным протоколам. "
                    "И согласно военному уставу, **запрещено** направлять служебные приветствия самому себе."
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
            dm_sent = False  # у пользователя закрыты ЛС

        # Эмбед-ответ автору клика
        reply_embed = disnake.Embed(
            title=f"<:sms:1533371911411732480> Защищённая радиограмма отправлена для {target_user.display_name}",
            description=(
                "Военная радиостанция успешно **обработала ваш запрос** и передала приветствие по защищённому каналу связи. "
                f"И командный центр **подтверждает**, что получатель {target_user.mention} получил сообщение."
            ),
            color=self.embed_color,
        )

        if not dm_sent:
            reply_embed = invalid_input_embed(self.embed_color, admins_mentions)

        await inter.edit_original_response(embed=reply_embed)
        