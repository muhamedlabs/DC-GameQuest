import os
import disnake
from disnake.ext import commands

from BANNED_FILES.config import Cybersecurity_Image, Embed_Color, GROUP_MODER_IDS, BLOCK_MESSAGE, BLOCK_MESSAGE_TOXIS, BLOCK_MESSAGE_LINKS, BLOCK_MESSAGE_SCAM, BLOCK_MESSAGE_SPAM, RULE_PREFIX, TOXIC_WORDS, LINK_FILTER, SCAM_WORDS, SPAM_WORDS
from commands.information_cog.warnings import no_access_embed


RULE_DEFINITIONS = {
    "threats": f"{RULE_PREFIX} • Анализ угроз",
    "lexical": f"{RULE_PREFIX} • Лексический фильтр",
    "links":   f"{RULE_PREFIX} • Контроль ссылок",
    "fishing": f"{RULE_PREFIX} • Антифишинг",
    "spam":    f"{RULE_PREFIX} • Антиспам",
}

RULE_LABELS = {
    "threats": "Анализ угроз",
    "lexical": "Лексический фильтр",
    "links":   "Контроль ссылок",
    "fishing": "Антифишинг",
    "spam":    "Антиспам",
}


def has_automod_role():
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        if not GROUP_MODER_IDS:
            return inter.author.guild_permissions.manage_guild
        return any(role.id in GROUP_MODER_IDS for role in inter.author.roles)
    return commands.check(predicate)


class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.image_path = Cybersecurity_Image if os.path.exists(Cybersecurity_Image) else None

    def _make_file(self) -> disnake.File | None:
        if self.image_path:
            return disnake.File(self.image_path, filename="banner.jpg")
        return None

    def create_embed(self, title: str, description: str, color: disnake.Color | None = None) -> disnake.Embed:
        embed = disnake.Embed(
            title=title,
            description=description,
            color=color or self.embed_color,
        )
        if self.image_path:
            embed.set_image(url="attachment://banner.jpg")
        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
        return embed

    async def create_rules(self, guild: disnake.Guild):
        await guild.create_automod_rule(
            name=RULE_DEFINITIONS["threats"],
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword_preset,
            trigger_metadata=disnake.AutoModTriggerMetadata(
                presets=(
                    disnake.AutoModKeywordPresets.profanity
                    | disnake.AutoModKeywordPresets.sexual_content
                    | disnake.AutoModKeywordPresets.slurs
                )
            ),
            actions=[disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE)],
            enabled=True,
        )
        await guild.create_automod_rule(
            name=RULE_DEFINITIONS["lexical"],
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword,
            trigger_metadata=disnake.AutoModTriggerMetadata(keyword_filter=TOXIC_WORDS),
            actions=[disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE_TOXIS)],
            enabled=True,
        )
        await guild.create_automod_rule(
            name=RULE_DEFINITIONS["links"],
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword,
            trigger_metadata=disnake.AutoModTriggerMetadata(keyword_filter=LINK_FILTER),
            actions=[disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE_LINKS)],
            enabled=True,
        )
        await guild.create_automod_rule(
            name=RULE_DEFINITIONS["fishing"],
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword,
            trigger_metadata=disnake.AutoModTriggerMetadata(keyword_filter=SCAM_WORDS),
            actions=[disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE_SCAM)],
            enabled=True,
        )
        await guild.create_automod_rule(
            name=RULE_DEFINITIONS["spam"],
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword,
            trigger_metadata=disnake.AutoModTriggerMetadata(keyword_filter=SPAM_WORDS),
            actions=[disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE_SPAM)],
            enabled=True,
        )

    def _build_status_embed(self, rules: list, title: str, description_header: str) -> tuple[disnake.Embed, disnake.File | None]:
        active_names   = {r.name for r in rules if r.enabled}
        inactive_names = {r.name for r in rules if not r.enabled}
        active_count   = len(active_names & set(RULE_DEFINITIONS.values()))
        inactive_count = len(inactive_names & set(RULE_DEFINITIONS.values()))
        total          = len(RULE_DEFINITIONS)

        lines = [description_header, ""]
        lines.append("**Компоненты оборонного комплекса:**")

        for key, name in RULE_DEFINITIONS.items():
            if name in active_names:
                status = "<:oncircle:1522866359350853692>"
            elif name in inactive_names:
                status = "<:offcircle:1522866355856998441>"
            else:
                status = "<:settings:1522866360567337010>"
            lines.append(f"{status} {RULE_LABELS[key]}")

        lines.append("")
        lines.append(f"**Активно:** {active_count}/{total}")

        return self.create_embed(title=title, description="\n".join(lines)), self._make_file()

    async def _send(self, inter: disnake.ApplicationCommandInteraction, embed: disnake.Embed, file: disnake.File | None):
        """Відправляє embed з файлом якщо є, без файлу якщо немає."""
        if file:
            await inter.edit_original_response(embed=embed, file=file)
        else:
            await inter.edit_original_response(embed=embed)

    @commands.slash_command(
        name="automod",
        description="Управление системой защиты сервера",
    )
    @commands.contexts(bot_dm=False, guild=True)
    @commands.default_member_permissions(manage_messages=True, moderate_members=True, administrator=True)
    
    @has_automod_role()
    async def automod(
        self,
        inter: disnake.ApplicationCommandInteraction,
        action: str = commands.Param(
            name="режим",
            description="Выберите режим работы системы защиты",
            choices={
                "Активировать": "enable",
                "Деактивировать": "disable",
            },
        ),
    ):
        await inter.response.defer(ephemeral=False)
        rules = await inter.guild.fetch_automod_rules()

        # ── Активировать ─────────────────────────────────────────────────────
        if action == "enable":
            if any(rule.name.startswith(RULE_PREFIX) for rule in rules):
                embed, file = self._build_status_embed(
                    rules=rules,
                    title="<:security:1522868634941390960> Оборонительный контур уже развернут",
                    description_header=(
                        ">>> Система безопасности **уже находится** в режиме полной боевой готовности и непрерывного мониторинга всех критических процессов. Повторная активация не требуется, поскольку текущий **протокол защиты** уже запущен и функционирует."
                    ),
                )
                return await self._send(inter, embed, file)

            await self.create_rules(inter.guild)
            rules = await inter.guild.fetch_automod_rules()

            embed, file = self._build_status_embed(
                rules=rules,
                title="<:shieldtick:1387113358389547138> Оборонительный контур активирован",
                description_header=">>> Центральный командный **узел обработал** поступивший запрос в полном объёме, выполнил многоуровневую проверку входящих данных, **сопоставил** результаты с актуальными протоколами безопасности.",
            )
            return await self._send(inter, embed, file)

        # ── Деактивировать ───────────────────────────────────────────────────
        deleted = 0
        for rule in rules:
            if rule.name.startswith(RULE_PREFIX):
                await rule.delete()
                deleted += 1

        deactivated_lines = [">>> Центральный командный **узел завершил** комплексную диагностику всего контура системы безопасности, включая анализ стабильности протоколов защиты, **проверку** состояния активных модулей мониторинга.\n"]
        deactivated_lines.append("**Компоненты оборонного комплекса:**")
        for label in RULE_LABELS.values():
            deactivated_lines.append(f"<:settings:1522866360567337010> {label}")
        deactivated_lines.append("")
        deactivated_lines.append(f"**Активно:** 0/{len(RULE_DEFINITIONS)}")

        embed = self.create_embed(
            title="<:shieldcross:1387113344908923125> Оборонительный контур отключён",
            description="\n".join(deactivated_lines),
        )
        await self._send(inter, embed, self._make_file())

    @automod.error
    async def automod_error(self, inter: disnake.ApplicationCommandInteraction, error: Exception):

        owner = inter.guild.owner.mention if inter.guild and inter.guild.owner else "Не назначен"

        if isinstance(error, commands.CheckFailure):

            embed = no_access_embed(self.embed_color, owner)

            if inter.response.is_done():
                await inter.followup.send(embed=embed, ephemeral=True)
            else:
                await inter.response.send_message(embed=embed, ephemeral=True)