import os
import random
import asyncio

import disnake
from disnake import ui
from disnake.ext import commands
from disnake.errors import DiscordServerError, HTTPException

from BANNED_FILES.config import Music_Images, Embed_Color

from commands.button_cog.button_id import ButtonID
from commands.button_cog.music_button import MusicCustomTrack


def _build_music_button(
    style: disnake.ButtonStyle = disnake.ButtonStyle.green,
) -> disnake.ui.Button:

    button = disnake.ui.Button(
        label="Музыка по спецзаказу",
        emoji=disnake.PartialEmoji(name="musicfilter", id=1535590395981987860),
        style=style,
        custom_id=ButtonID.MUSIC_CUSTOM_TRACK.value,
    )

    button.callback = MusicCustomTrack

    return button


class MusicView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(_build_music_button())


class MusicIntegration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.message: disnake.Message | None = None

        self.embed_image_path: str | None = None
        self.embed_image_filename: str | None = None

        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    async def cog_load(self):

        self.bot.add_view(
            MusicView()
        )

    def _clean_track_name(self, track_name: str) -> str:
        return os.path.splitext(track_name)[0]

    def _pick_random_image(self) -> str:
        images = [
            filename
            for filename in os.listdir(Music_Images)
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif"))
            and filename != "Music_art_1.png"
        ]

        chosen = random.choice(images)

        return os.path.join(Music_Images, chosen)

    def _pick_image(self, track_name: str) -> str:
        if track_name == "Ожидание музыки...":
            return os.path.join(Music_Images, "Music_art_1.png")

        return self._pick_random_image()

    def build_components(
        self,
        track_name: str,
        custom: bool = False,
        requester: disnake.Member | None = None,
    ):
        if custom:
            title = (
                "## <:playlis:1390972178622582856> Радиостанция военной базы — специальный эфир"
            )

            requester_line = (
                f"<:usersquar:1388889541645172957> **Спецзаказ лейтенанта:** {requester.mention}"
                if requester
                else ""
            )

            description = (
                "> Штабная радиостанция **получила** специальный запрос от личного состава "
                "и распоряжением командования **вывела его в эфир** вне установленной очереди.\n\n" \
                f"{requester_line}\n"
                f"<:musicnote:1535912846716829756> **Активировано проигрывание композиции:**\n {track_name}"
            )

        elif track_name == "Ожидание музыки...":
            title = (
                "## <:playlis:1390972178622582856> Радиостанция военной базы — ожидание сигнала"
            )

            description = (
                "> Штабная радиостанция временно **находится** в режиме ожидания. "
                "Антенна **развёрнута**, частота настроена, канал связи проверяется."
            )

        else:
            title = (
                "## <:playlis:1390972178622582856> Радиостанция военной базы — прямой эфир"
            )

            clean_name = self._clean_track_name(track_name)

            description = (
                "> Штабная радиостанция **установила соединение** и перешла "
                "в режим **постоянного вещания** для всего гарнизона.\n\n"
                f"<:musicnote:1535912846716829756> **Активировано проигрывание композиции:**\n {clean_name}"
            )

        filename = self.embed_image_filename

        music_row = disnake.ui.ActionRow(
            _build_music_button()
        )

        container = ui.Container(
            ui.TextDisplay(
                title
            ),

            ui.Separator(
                divider=True
            ),

            ui.TextDisplay(
                description
            ),

            ui.MediaGallery(
                disnake.MediaGalleryItem(
                    media=f"attachment://{filename}"
                )
            ),

            ui.Separator(
                divider=True
            ),

            ui.TextDisplay(
                "-# Благодарим за проявленный интерес к нашему спецпроекту! "
                "И для заказа нажмите кнопку ниже.",
            ),

            music_row,

            accent_colour=self.embed_color,
        )

        return [container]

    async def send_or_update_message(
        self,
        track_name: str,
        channel: disnake.VoiceChannel,
        custom: bool = False,
        requester: disnake.Member | None = None,
    ):

        if channel is None:
            return

        if (
            self.message is not None
            and self.message.channel.id != channel.id
        ):
            await self.delete_message()

        self.embed_image_path = self._pick_image(track_name)
        self.embed_image_filename = os.path.basename(self.embed_image_path)

        components = self.build_components(
            track_name=track_name,
            custom=custom,
            requester=requester,
        )

        MAX_RETRIES = 3

        for attempt in range(
            1,
            MAX_RETRIES + 1,
        ):
            try:
                if self.message is None:

                    self.message = await channel.send(
                        components=components,
                        file=disnake.File(
                            self.embed_image_path,
                            filename=self.embed_image_filename,
                        ),
                        flags=disnake.MessageFlags(
                            is_components_v2=True
                        ),
                    )

                else:
                    await self.message.edit(
                        components=components,
                        file=disnake.File(
                            self.embed_image_path,
                            filename=self.embed_image_filename,
                        ),
                    )

                break

            except DiscordServerError as e:
                if e.status == 503:
                    await asyncio.sleep(
                        2 * attempt
                    )
                else:
                    break

            except disnake.NotFound:
                try:
                    self.message = await channel.send(
                        components=components,
                        file=disnake.File(
                            self.embed_image_path,
                            filename=self.embed_image_filename,
                        ),
                        flags=disnake.MessageFlags(
                            is_components_v2=True
                        ),
                    )
                except Exception:
                    pass

                break

            except HTTPException:
                break

            except Exception:
                break

    async def delete_message(self):
        if self.message is None:
            return

        try:
            await self.message.delete()

        except disnake.NotFound:
            pass

        except Exception:
            pass

        finally:
            self.message = None