import disnake
from disnake import ui
from disnake.ext import commands
import os

from BANNED_FILES.config import GREETING_CHANNEL_ID, MAIN_ROLE_ID, Welcome_Gif, Embed_Color
from commands.button_cog.button_id import ButtonID


def build_greet_button(target_id: int) -> disnake.ui.ActionRow:
    button = disnake.ui.Button(
        label="Поздороваться с лейтенантом",
        emoji=disnake.PartialEmoji(name="smstracking", id=1533371913106362469),
        style=disnake.ButtonStyle.green,
        custom_id=f"{ButtonID.GREET_USER_PREFIX.value}:{target_id}",
    )
    return disnake.ui.ActionRow(button)


class WelcomeHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.accent_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        # Выдача роли
        role = member.guild.get_role(MAIN_ROLE_ID)
        if role:
            await member.add_roles(role, reason="Присоединился к серверу")

        # Приветственная ветка
        try:
            welcome_channel = self.bot.get_channel(GREETING_CHANNEL_ID)

            if welcome_channel is None:
                welcome_channel = await self.bot.fetch_channel(GREETING_CHANNEL_ID)

            if not isinstance(welcome_channel, disnake.Thread):
                print(
                    f"[ERROR] GREETING_CHANNEL_ID ({GREETING_CHANNEL_ID}) "
                    f"не является веткой. Получен объект: "
                    f"{type(welcome_channel).__name__}"
                )
                return

            if welcome_channel.archived:
                await welcome_channel.edit(archived=False)

        except disnake.NotFound:
            print(
                f"[ERROR] Ветка с ID {GREETING_CHANNEL_ID} не найдена."
            )
            return

        except disnake.Forbidden:
            print(
                f"[ERROR] Недостаточно прав для доступа к ветке "
                f"{GREETING_CHANNEL_ID}."
            )
            return

        except disnake.HTTPException as e:
            print(
                f"[ERROR] Ошибка Discord API при получении ветки "
                f"{GREETING_CHANNEL_ID}: {e}"
            )
            return

        # Проверка гифки
        if not os.path.isfile(Welcome_Gif):
            print(f"[ERROR] GIF-файл '{Welcome_Gif}' не найден.")
            return

        filename = os.path.basename(Welcome_Gif)
        gif_file = disnake.File(Welcome_Gif, filename=filename)

        greet_row = build_greet_button(member.id)

        container = ui.Container(
            ui.TextDisplay(f"## <:enhance:1390972267504210062> Здравия желаю, лейтенант {member.display_name}"),
            ui.Separator(divider=True),
            ui.TextDisplay(
                f"> Ознакомьтесь с **правилами сервера** и загляните в разделы **навигации**, {member.mention}. "
                "Там ждёт много полезного и увлекательного контента.\n\n"
                "Не упустите возможность **познакомиться** с другими участниками — "
                "за каждым никнеймом скрывается своя уникальная **история** и интересы!\n\n"
                "<:lock:1528278435913535488> Для получения **полного доступа** к серверу пройдите верификацию "
                "с помощью команды: `/идентификация`"
            ),
            ui.MediaGallery(
                disnake.MediaGalleryItem(media=f"attachment://{filename}")
            ),
            ui.Separator(divider=True),
            ui.TextDisplay("-# Благодарим за проявленный интерес к спецпроекту! И передайте приветствие кнопку ниже."
            ),

            greet_row,
            accent_colour=self.accent_color,
        )

        try:
            await welcome_channel.send(
                components=[container],
                file=gif_file,
                flags=disnake.MessageFlags(is_components_v2=True),
            )

        except disnake.Forbidden:
            print(
                f"[ERROR] Нет прав для отправки сообщения в ветку "
                f"{welcome_channel.name} ({welcome_channel.id})."
            )

        except disnake.HTTPException as e:
            print(
                f"[ERROR] Не удалось отправить сообщение в ветку "
                f"{welcome_channel.name} ({welcome_channel.id}): {e}"
            )
