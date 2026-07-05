import disnake

from BANNED_FILES.config import ALLOWED_USER_IDS


async def send_text(self, inter: disnake.ApplicationCommandInteraction):
    owner = inter.guild.owner.mention if inter.guild and inter.guild.owner else "Не назначен"
    admins_mentions = " ".join(f"<@{uid}>" for uid in ALLOWED_USER_IDS)

    return owner, admins_mentions


# Доступ запрещён
def no_access_embed(color, owner):
    return disnake.Embed(
        title="<:forbidden:1390972224436965386> Доступ к команде заблокирован",
        description=(
            "Проверка полномочий завершена. И у вас **отсутствует необходимый уровень допуска** "
            "для выполнения данного приказа.\n\n"
            f">>> Если вы считаете, что это ошибка — свяжитесь с командующим базы: {owner}"
        ),
        color=color,
    )


# Ошибка допуска
def system_error_embed(color, owner):
    return disnake.Embed(
        title="<:forbidden:1390972224436965386> Ошибка идентификации оператора",
        description=(
            "Система безопасности **не смогла** подтвердить вашу личность. "
            "Выполнение операции автоматически **отменено**.\n\n"
            f">>> Если проблема сохраняется — сообщите командующему базы: {owner}"
        ),
        color=color,
    )


# Критическая ошибка
def critical_error_embed(color, admins_mentions):
    return disnake.Embed(
        title="<:forbidden:1390972224436965386> Критический системный сбой",
        description=(
            "Во время выполнения операции произошла **внутренняя ошибка** командного комплекса. "
            "Обработка команды была немедленно **остановлена**.\n\n"
            f">>> Передайте отчёт инженерному подразделению: {admins_mentions}"
        ),
        color=color,
    )


# Защитный протокол
def security_block_embed(color, owner):
    return disnake.Embed(
        title="<:forbidden:1390972224436965386> Защитный протокол активирован",
        description=(
            "Система безопасности **заблокировала** выполнение операции. "
            "Текущий уровень допуска не соответствует **требованиям**.\n\n"
            f">>> Для получения разрешения обратитесь к командующему базы: {owner}"
        ),
        color=color,
    )


# Ошибка данных
def invalid_input_embed(color, admins_mentions):
    return disnake.Embed(
        title="<:forbidden:1390972224436965386> Ошибка обработки данных",
        description=(
            "Переданные **параметры содержат ошибки** или неполные данные. "
            "Выполнение операции невозможно.\n\n"
            f">>> Проверьте введённые данные или обратитесь в инженерное подразделение: {admins_mentions}"
        ),
        color=color,
    )