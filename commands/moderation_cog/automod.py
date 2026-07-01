import disnake
from disnake.ext import commands

from BANNED_FILES.config import GROUP_MODER_IDS, BLOCK_MESSAGE, RULE_PREFIX, TOXIC_WORDS, LINK_FILTER, SCAM_WORDS, SPAM_WORDS

# ───────────────────────── CHECK ─────────────────────────

def has_automod_role():
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        if not GROUP_MODER_IDS:
            return inter.author.guild_permissions.manage_guild
        return any(r.id in GROUP_MODER_IDS for r in inter.author.roles)

    return commands.check(predicate)


# ───────────────────────── COG ─────────────────────────

class AutoMod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ───────────────────────── CREATE RULES ─────────────────────────

    async def create_rules(self, guild: disnake.Guild):

        # 🛡 PRESETS
        await guild.create_automod_rule(
            name=f"{RULE_PREFIX} Presets",
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword_preset,
            trigger_metadata=disnake.AutoModTriggerMetadata(
                presets=(
                    disnake.AutoModKeywordPresets.profanity
                    | disnake.AutoModKeywordPresets.sexual_content
                    | disnake.AutoModKeywordPresets.slurs
                )
            ),
            actions=[
                disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE)
            ],
            enabled=True,
        )

        # 🚫 TOXIC WORDS
        await guild.create_automod_rule(
            name=f"{RULE_PREFIX} Keywords",
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword,
            trigger_metadata=disnake.AutoModTriggerMetadata(
                keyword_filter=TOXIC_WORDS
            ),
            actions=[
                disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE)
            ],
            enabled=True,
        )

        # 🔗 LINKS + INVITES
        await guild.create_automod_rule(
            name=f"{RULE_PREFIX} Links",
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword,
            trigger_metadata=disnake.AutoModTriggerMetadata(
                keyword_filter=LINK_FILTER
            ),
            actions=[
                disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE)
            ],
            enabled=True,
        )

        # 💰 SCAM
        await guild.create_automod_rule(
            name=f"{RULE_PREFIX} Scam",
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword,
            trigger_metadata=disnake.AutoModTriggerMetadata(
                keyword_filter=SCAM_WORDS
            ),
            actions=[
                disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE)
            ],
            enabled=True,
        )

        # ⚡ SPAM
        await guild.create_automod_rule(
            name=f"{RULE_PREFIX} Spam",
            event_type=disnake.AutoModEventType.message_send,
            trigger_type=disnake.AutoModTriggerType.keyword,
            trigger_metadata=disnake.AutoModTriggerMetadata(
                keyword_filter=SPAM_WORDS
            ),
            actions=[
                disnake.AutoModBlockMessageAction(custom_message=BLOCK_MESSAGE)
            ],
            enabled=True,
        )

    # ───────────────────────── COMMAND ─────────────────────────

    @commands.slash_command(
        name="automod",
        description="Toggle AutoMod system"
    )
    @has_automod_role()
    async def automod(
        self,
        inter: disnake.ApplicationCommandInteraction,
        action: str = commands.Param(choices=["enable", "disable"]),
    ):
        await inter.response.defer(ephemeral=True)

        rules = await inter.guild.fetch_automod_rules()

        # ───────── ENABLE ─────────
        if action == "enable":

            if any(r.name.startswith(RULE_PREFIX) for r in rules):
                return await inter.edit_original_response(
                    embed=disnake.Embed(
                        description="⚠️ AutoMod already enabled",
                        color=disnake.Color.green(),
                    )
                )

            await self.create_rules(inter.guild)

            return await inter.edit_original_response(
                embed=disnake.Embed(
                    title="🛡 AutoMod Enabled",
                    description="All rules loaded from config",
                    color=disnake.Color.green(),
                )
            )

        # ───────── DISABLE ─────────
        deleted = 0

        for r in rules:
            if r.name.startswith(RULE_PREFIX):
                await r.delete()
                deleted += 1

        return await inter.edit_original_response(
            embed=disnake.Embed(
                title="🧹 AutoMod Disabled",
                description=f"Deleted {deleted} rules",
                color=disnake.Color.red(),
            )
        )
