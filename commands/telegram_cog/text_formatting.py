import re
from typing import Union, List, Tuple, Dict, Any
from telethon import helpers
from telethon.tl.types import (
    MessageEntityBold, MessageEntityItalic, MessageEntityTextUrl,
    MessageEntityUrl, MessageEntityCode, MessageEntityPre,
    MessageEntityUnderline, MessageEntityStrike, MessageEntitySpoiler,
    MessageEntityBlockquote, MessageEntityMention, MessageEntityMentionName,
    MessageEntityHashtag, MessageEntityCashtag, MessageEntityBotCommand,
    MessageEntityEmail, MessageEntityPhone, MessageEntityCustomEmoji
)

EntityType = Union[
    MessageEntityBold, MessageEntityItalic, MessageEntityTextUrl,
    MessageEntityUrl, MessageEntityCode, MessageEntityPre,
    MessageEntityUnderline, MessageEntityStrike, MessageEntitySpoiler,
    MessageEntityBlockquote, MessageEntityMention, MessageEntityMentionName,
    MessageEntityHashtag, MessageEntityCashtag, MessageEntityBotCommand,
    MessageEntityEmail, MessageEntityPhone, MessageEntityCustomEmoji
]


def escape_markdown(text: str, escape_brackets: bool = True) -> str:
    """Экранирует специальные символы markdown"""
    if escape_brackets:
        return re.sub(r'([\\`*_~[\]()])', r'\\\1', text)
    else:
        return re.sub(r'([\\`*_~\]])', r'\\\1', text)


def get_markdown_tag(entity: EntityType) -> str:
    """Возвращает markdown тег для entity"""
    if isinstance(entity, MessageEntityBold):
        return "**"
    elif isinstance(entity, MessageEntityItalic):
        return "*"
    elif isinstance(entity, MessageEntityUnderline):
        return "__"
    elif isinstance(entity, MessageEntityStrike):
        return "~~"
    elif isinstance(entity, MessageEntityCode):
        return "`"
    elif isinstance(entity, MessageEntityPre):
        return "```"
    elif isinstance(entity, MessageEntitySpoiler):
        return "||"  # Discord spoiler format
    # Blockquote больше не обрабатывается тут — см. format_telegram_message
    return ""


def get_special_formatting(entity: EntityType, text: str) -> str:
    """Возвращает специальное форматирование для особых типов entity"""
    if isinstance(entity, MessageEntityMention):
        return text  # Оставляем как есть @username
    elif isinstance(entity, MessageEntityMentionName):
        # Для именованных упоминаний показываем текст как есть
        return text
    elif isinstance(entity, MessageEntityHashtag):
        return f"#{text.lstrip('#')}"  # Убеждаемся что есть #
    elif isinstance(entity, MessageEntityCashtag):
        return f"${text.lstrip('$')}"  # Убеждаемся что есть $
    elif isinstance(entity, MessageEntityBotCommand):
        return f"/{text.lstrip('/')}"  # Убеждаемся что есть /
    elif isinstance(entity, MessageEntityEmail):
        return f"<{text}>"  # Обрамляем email в скобки
    elif isinstance(entity, MessageEntityPhone):
        return f"`{text}`"  # Форматируем телефон как код
    elif isinstance(entity, MessageEntityUrl):
        return text  # Обычная ссылка — пусть Discord сам показывает превью, как для любой ссылки
    return text


def mask_url_for_discord(url: str) -> str:
    """Маскирует URL чтобы Discord не создавал автоматические превью"""
    return url.replace('.', '․')  # Используем схожий Unicode символ


def _split_edge_whitespace(text: str) -> Tuple[str, str, str]:
    """
    Отделяет пробельные символы (включая \\n) с краёв текста от "ядра".
    Нужно, чтобы markdown-теги (**, __, `` ` `` и т.д.) и скобки ссылки [ ]
    никогда не оказывались рядом с пробелом изнутри — Discord (в отличие от
    самого Telegram) не считает **so **этим bold, если сразу после ** идёт
    пробел. Telegram может присылать entity, чей offset/length честно
    захватывает такой пробел (например, если админ в Telegram выделил
    " Текст" вместе с пробелом) — Telegram это рисует жирным, Discord — нет.
    Возвращает (leading_ws, core, trailing_ws).
    """
    if not text or not text.strip():
        return text, "", ""
    leading_ws = text[:len(text) - len(text.lstrip())]
    trailing_ws = text[len(text.rstrip()):]
    core = text[len(leading_ws): len(text) - len(trailing_ws)] if trailing_ws else text[len(leading_ws):]
    return leading_ws, core, trailing_ws


class TextSegment:
    """Класс для представления сегмента текста с форматированием"""

    def __init__(self, start: int, end: int, text: str):
        self.start = start
        self.end = end
        self.text = text
        self.format_tags = []  # Список тегов форматирования
        self.is_link = False
        self.link_url = ""
        self.link_entities = []  # Entities внутри ссылки
        self.special_entities = []  # Специальные entities (mentions, hashtags, etc.)

    def add_format_tag(self, tag: str):
        if tag not in self.format_tags:
            self.format_tags.append(tag)

    def set_as_link(self, url: str, entities: List[EntityType]):
        self.is_link = True
        self.link_url = url
        self.link_entities = entities

    def add_special_entity(self, entity: EntityType):
        self.special_entities.append(entity)


def build_segments(text: str, entities: List[EntityType]) -> List[TextSegment]:
    """Строит список сегментов текста с учетом всех entities"""
    if not text:
        return []

    # Собираем все позиции где происходят изменения
    positions = set([0, len(text)])

    for entity in entities:
        start = max(0, entity.offset)
        end = min(len(text), entity.offset + entity.length)
        if start < end:
            positions.add(start)
            positions.add(end)

    positions = sorted(positions)

    # Создаем базовые сегменты
    segments = []
    for i in range(len(positions) - 1):
        start = positions[i]
        end = positions[i + 1]
        if start < end:
            segment_text = text[start:end]
            segments.append(TextSegment(start, end, segment_text))

    # Применяем форматирование к сегментам
    for entity in entities:
        entity_start = max(0, entity.offset)
        entity_end = min(len(text), entity.offset + entity.length)

        if entity_start >= entity_end:
            continue

        if isinstance(entity, MessageEntityTextUrl):
            # Обрабатываем ссылки особым образом
            affected_segments = [s for s in segments
                                  if s.start >= entity_start and s.end <= entity_end]

            # Находим entities внутри ссылки
            inner_entities = [
                e for e in entities
                if (not isinstance(e, (MessageEntityTextUrl, MessageEntityUrl)) and
                    e.offset >= entity_start and
                    e.offset + e.length <= entity_end)
            ]

            for segment in affected_segments:
                segment.set_as_link(entity.url, inner_entities)

        elif isinstance(entity, MessageEntityBlockquote):
            # Цитаты теперь считаются отдельно по диапазонам в format_telegram_message,
            # чтобы не резать текст цитаты на сегменты (иначе "> " может попасть
            # в середину строки, если границы blockquote и, например, bold не совпадают)
            continue

        elif isinstance(entity, (MessageEntityMention, MessageEntityMentionName,
                                  MessageEntityHashtag, MessageEntityCashtag,
                                  MessageEntityBotCommand, MessageEntityEmail,
                                  MessageEntityPhone, MessageEntityUrl)):
            # Специальные entities
            for segment in segments:
                if (segment.start >= entity_start and segment.end <= entity_end):
                    segment.add_special_entity(entity)

        else:
            # Обычное форматирование
            tag = get_markdown_tag(entity)
            if tag:
                for segment in segments:
                    if (segment.start >= entity_start and segment.end <= entity_end):
                        segment.add_format_tag(tag)

    return segments


def format_segment(segment: TextSegment, discord_mode: bool = True, hide_urls: bool = False) -> str:
    """Форматирует один сегмент текста (блокквоуты сюда не входят — см. format_telegram_message)"""
    if segment.is_link:
        # Для ссылок применяем форматирование внутри и делаем их кликабельными
        if segment.link_entities:
            formatted_text = segment.text

            # Применяем теги форматирования внутри ссылки
            for entity in segment.link_entities:
                rel_start = max(0, entity.offset - segment.start)
                rel_end = min(len(segment.text), entity.offset + entity.length - segment.start)

                if rel_start < rel_end and rel_start < len(formatted_text):
                    tag = get_markdown_tag(entity)
                    if tag:
                        # Применяем тег к соответствующей части текста
                        before = formatted_text[:rel_start]
                        middle = formatted_text[rel_start:rel_end]
                        after = formatted_text[rel_end:]
                        formatted_text = f"{before}{tag}{middle}{tag}{after}"
        else:
            # Без вложенного форматирования — экранируем текст ссылки,
            # иначе символы вроде ] или * ломают markdown-синтаксис [текст](url)
            formatted_text = escape_markdown(segment.text)

        # Пробелы по краям выносим ЗА пределы [ ], иначе получаем "[ текст]"
        # (Telegram-entity ссылки иногда честно включает такой пробел)
        leading_ws, core, trailing_ws = _split_edge_whitespace(formatted_text)

        if not core:
            # Сегмент — сплошной пробел, оформлять как ссылку нечего
            return formatted_text

        url = mask_url_for_discord(segment.link_url) if hide_urls else segment.link_url
        return f"{leading_ws}[{core}]({url}){trailing_ws}"

    else:
        # Обрабатываем специальные entities
        formatted_text = segment.text
        for entity in segment.special_entities:
            formatted_text = get_special_formatting(entity, formatted_text)

        # Если нет специальных entities, экранируем markdown
        if not segment.special_entities:
            formatted_text = escape_markdown(formatted_text, escape_brackets=True)

        if not segment.format_tags:
            return formatted_text

        # Пробелы по краям выносим ЗА пределы тегов форматирования, иначе
        # "** текст**" не распознаётся Discord/CommonMark как bold (в отличие
        # от самого Telegram, которому пробел рядом с границей entity не мешает)
        leading_ws, core, trailing_ws = _split_edge_whitespace(formatted_text)

        if not core:
            # Сегмент — сплошной пробел/перенос строки, обрамлять нечего
            return formatted_text

        # Применяем теги форматирования
        # Сортируем теги по длине (длинные первыми для правильного вложения)
        sorted_tags = sorted(segment.format_tags, key=len, reverse=True)

        for tag in sorted_tags:
            core = f"{tag}{core}{tag}"

        return f"{leading_ws}{core}{trailing_ws}"


def _apply_blockquotes(surrogated_text: str, formatted_full: str, entities: List[EntityType]) -> str:
    """
    Добавляет "> " построчно к тем строкам, которые попадают в диапазон
    MessageEntityBlockquote. Делается ПОСЛЕ сборки готового форматированного
    текста, а не на уровне отдельных сегментов — теги форматирования (**, *,
    __, ` и т.д.) никогда не содержат '\\n', поэтому количество строк в
    formatted_full всегда совпадает с количеством строк в surrogated_text,
    и построчное сопоставление безопасно.
    """
    blockquote_ranges = [
        (max(0, e.offset), min(len(surrogated_text), e.offset + e.length))
        for e in entities if isinstance(e, MessageEntityBlockquote)
    ]

    if not blockquote_ranges:
        return formatted_full

    quoted_flags = []
    pos = 0
    for line in surrogated_text.split('\n'):
        line_start, line_end = pos, pos + len(line)
        is_quoted = any(
            not (line_end <= qs or line_start >= qe)  # пересечение строки с диапазоном цитаты
            for qs, qe in blockquote_ranges
        )
        quoted_flags.append(is_quoted)
        pos = line_end + 1  # +1 за символ '\n'

    output_lines = formatted_full.split('\n')

    # На случай рассинхрона количества строк (не должно происходить, но подстрахуемся)
    if len(output_lines) != len(quoted_flags):
        return formatted_full

    for i, is_quoted in enumerate(quoted_flags):
        if is_quoted:
            output_lines[i] = f"> {output_lines[i]}"

    return '\n'.join(output_lines)


def format_telegram_message(text: str, entities: List[EntityType]) -> str:
    """
    Конвертирует Telegram сообщение с entities в markdown формат для Discord
    Создает кликабельные ссылки внутри текста с сохранением форматирования
    """
    if not text:
        return ""

    if not entities:
        return escape_markdown(text)

    # Telegram считает entity.offset/length в UTF-16 code units, а не в символах
    # Python. Если перед сущностью (ссылкой, жирным текстом и т.д.) встречается
    # символ вне BMP (например, эмодзи — 2 code unit в UTF-16, но 1 символ в
    # Python), обычная индексация "съезжает" на 1+ символ для всего, что идёт
    # после него. add_surrogate превращает такие символы в суррогатные пары,
    # чтобы срез по offset/length совпадал с тем, что имел в виду Telegram.
    surrogated_text = helpers.add_surrogate(text)

    # Строим сегменты
    segments = build_segments(surrogated_text, entities)

    # Форматируем каждый сегмент (без учёта цитат — их накладываем ниже)
    formatted_full = ''.join(format_segment(s) for s in segments)

    # Накладываем "> " построчно по диапазонам blockquote-entities
    formatted_full = _apply_blockquotes(surrogated_text, formatted_full, entities)

    # Возвращаем суррогатные пары обратно в нормальные символы перед выдачей
    return helpers.del_surrogate(formatted_full)


def format_plain_text(text: str, preserve_formatting: bool = False) -> str:
    """
    Форматирует обычный текст без entities

    Args:
        text: Исходный текст
        preserve_formatting: Если True, сохраняет переносы строк и пробелы
    """
    if not text:
        return ""

    if preserve_formatting:
        # Сохраняем форматирование, только экранируем специальные символы
        return escape_markdown(text, escape_brackets=True)
    else:
        # Нормализуем пробелы и переносы строк
        normalized = re.sub(r'\s+', ' ', text.strip())
        return escape_markdown(normalized, escape_brackets=True)


def format_code_block(text: str, language: str = "") -> str:
    """Форматирует текст как блок кода"""
    if language:
        return f"```{language}\n{text}\n```"
    else:
        return f"```\n{text}\n```"


def format_quote_block(text: str) -> str:
    """Форматирует текст как цитату"""
    lines = text.split('\n')
    quoted_lines = [f"> {line}" for line in lines]
    return '\n'.join(quoted_lines)


def format_spoiler_text(text: str) -> str:
    """Форматирует текст как спойлер"""
    return f"||{escape_markdown(text)}||"


def format_list(items: List[str], ordered: bool = False) -> str:
    """Форматирует список элементов"""
    formatted_items = []
    for i, item in enumerate(items, 1):
        escaped_item = escape_markdown(item)
        if ordered:
            formatted_items.append(f"{i}. {escaped_item}")
        else:
            formatted_items.append(f"• {escaped_item}")

    return '\n'.join(formatted_items)


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Форматирует простую таблицу (Discord не поддерживает таблицы, но можно сделать читаемый формат)"""
    if not headers or not rows:
        return ""

    # Экранируем содержимое
    escaped_headers = [escape_markdown(h) for h in headers]
    escaped_rows = [[escape_markdown(cell) for cell in row] for row in rows]

    # Находим максимальную ширину для каждой колонки
    col_widths = [len(h) for h in escaped_headers]
    for row in escaped_rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))

    # Форматируем как код блок
    lines = []

    # Заголовки
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(escaped_headers))
    lines.append(header_line)

    # Разделитель
    separator = "-+-".join("-" * w for w in col_widths)
    lines.append(separator)

    # Строки данных
    for row in escaped_rows:
        row_line = " | ".join(
            (cell if i < len(row) else "").ljust(col_widths[i])
            for i, cell in enumerate(row + [""] * (len(col_widths) - len(row)))
        )
        lines.append(row_line)

    return f"```\n{chr(10).join(lines)}\n```"


# Основные функции для использования
def format_for_discord(text: str, entities: List[EntityType] = None,
                        hide_urls: bool = False) -> str:
    """
    Форматирование Telegram сообщений для Discord

    Args:
        text: Исходный текст
        entities: Список entities (если None, обрабатывается как обычный текст)
        hide_urls: Если True, маскирует URLs чтобы избежать превью
    """
    if entities:
        return format_telegram_message(text, entities)
    else:
        return format_plain_text(text)


# Для обратной совместимости
def apply_formatting(text: str, entities: List[EntityType], base_offset: int = 0,
                      escape_brackets: bool = True) -> str:
    """Устаревшая функция, используйте format_for_discord"""
    return format_telegram_message(text, entities)


# Дополнительные утилиты
def combine_messages(messages: List[Tuple[str, List[EntityType]]],
                      separator: str = "\n\n") -> str:
    """Объединяет несколько сообщений в одно отформатированное"""
    formatted_parts = []
    for text, entities in messages:
        formatted = format_for_discord(text, entities)
        if formatted.strip():
            formatted_parts.append(formatted)

    return separator.join(formatted_parts)


def truncate_message(text: str, max_length: int = 2000, suffix: str = "...") -> str:
    """Обрезает сообщение до указанной длины (лимит Discord)"""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix