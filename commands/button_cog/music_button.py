import re

import disnake

from .button_id import ButtonID
from BANNED_FILES.config import Embed_Color


YOUTUBE_RE = re.compile(
    r"^https?://"
    r"(www\.)?"
    r"(youtube\.com/watch\?v=|youtu\.be/|music\.youtube\.com/watch\?v=)"
)


def _embed(
    title: str,
    description: str,
) -> disnake.Embed:
    embed = disnake.Embed(
        title=title,
        description=description,
        color=disnake.Color(
            int(Embed_Color.lstrip("#"), 16)
        ),
    )

    return embed


async def _send_embed(
    inter: disnake.Interaction,
    title: str,
    description: str,
):
    await inter.response.send_message(
        embed=_embed(
            title,
            description,
        ),
        ephemeral=True,
    )


class CustomTrackModal(disnake.ui.Modal):
    def __init__(self):
        components = [
            disnake.ui.TextInput(
                label="Ссылка на музыку в YouTube",
                custom_id="youtube_url",
                style=disnake.TextInputStyle.short,
                placeholder="https://youtu.be/PHw0iNSi7WQ",
                max_length=200,
            )
        ]

        super().__init__(
            title="Музыка по спецзаказу",
            components=components,
        )

    async def callback(
        self,
        inter: disnake.ModalInteraction,
    ):
        url = inter.text_values[
            "youtube_url"
        ].strip()

        if not YOUTUBE_RE.match(url):
            await _send_embed(
                inter,
                "<:musicsquareremove:1535597559911817286> Позывной не распознан",
                (
                    "Штабной приёмник не смог опознать переданный позывной — ссылка не соответствует протоколу вещания YouTube."
                ),
            )
            return

        music_player = inter.bot.get_cog(
            "MusicPlayer"
        )

        if music_player is None:
            await _send_embed(
                inter,
                "<:musicsquareremove:1535597559911817286> Узел связи не отвечает",
                (
                    "Модуль музыкального вещания на этом сервере в данный момент не загружен — связь со штабом временно прервана."
                ),
            )
            return

        ok, text = await music_player.submit_custom_track(
            url,
            inter.author,
        )

        if ok:
            title = (
                "<:musicsquareadd:1535597558624157777> "
                "Заявка принята штабом"
            )

            description = (
                "Радист зафиксировал заявку и передал её дежурному по "
                f"эфиру.\n\n{text}"
            )

        else:
            title = (
                "<:musicsquareremove:1535597559911817286> "
                "Заявка отклонена штабом"
            )

            description = (
                "Дежурный по эфиру рассмотрел заявку и вынес отказ.\n\n"
                f"{text}"
            )

        await _send_embed(
            inter,
            title,
            description,
        )


async def MusicCustomTrack(
    inter: disnake.MessageInteraction,
):
    if (
        inter.component.custom_id
        != ButtonID.MUSIC_CUSTOM_TRACK.value
    ):
        return

    music_player = inter.bot.get_cog(
        "MusicPlayer"
    )

    if (
        music_player is None
        or music_player.is_disconnected()
    ):
        await _send_embed(
            inter,
            "<:musicsquareremove:1535597559911817286> Эфир не в сети",
            (
                "Радиостанция сектора в данный момент не ведёт вещание — передатчик отключён, канал связи молчит."
            ),
        )
        return

    voice_client = music_player.voice_client

    if (
        voice_client is None
        or voice_client.channel is None
    ):
        await _send_embed(
            inter,
            "<:musicsquareremove:1535597559911817286> Эфир не в сети",
            (
                "Радиостанция сектора сейчас не подключена ни к одному голосовому каналу — передатчик находится в режиме ожидания."
            ),
        )
        return

    voice_state = inter.author.voice

    if (
        not voice_state
        or not voice_state.channel
        or voice_state.channel.id
        != voice_client.channel.id
    ):
        await _send_embed(
            inter,
            "<:musicsquareremove:1535597559911817286> Доступ ограничен",
            (
                "Подача заявок на спецэфир разрешена исключительно личному составу, **находящемуся в текущем голосовом канале вещания**.\n\n"
            ),
        )
        return

    if music_player.is_custom_busy():
        await _send_embed(
            inter,
            "<:musicsquaresearch:1535597561275093022> Канал занят",
            (
                "Очередь вещания уже занята другой заявкой — одновременно в эфир может быть поставлен только один внеплановый трек."
            ),
        )
        return

    await inter.response.send_modal(
        CustomTrackModal()
    )