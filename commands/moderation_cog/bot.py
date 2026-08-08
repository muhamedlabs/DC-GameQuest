from datetime import datetime, timedelta

import disnake
from disnake.ext import commands

from ashredis import MISSING
from BANNED_FILES.config import ALLOWED_USER_IDS, Community_Image, Embed_Color, GROUP_MODER_IDS, RedisManager
from commands.information_cog.time import current_time
from commands.information_cog.warnings import invalid_input_embed, no_access_embed, security_block_embed
from redis_storage.bot_blocking import BotBlocking


NOTICE_INTERVAL = timedelta(days=1)

ICON_INFO = "<:clipboardtext:1529193114345017515>"
ICON_BAN = "<:clipboardclose:1529193112138809456>"
ICON_UNBAN = "<:clipboardtick:1529193115947372805>"
ICON_NOTE = "<:note:1535559023762612344>"
ICON_NOTIFICATION = "<:notificationstatus:1535561232172585010>"

RANK = "Лейтенант"


class BotBan(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.blocked: dict[int, BotBlocking] = {}
        self.allowed_users = set(ALLOWED_USER_IDS)
        self.moder_ids = set(GROUP_MODER_IDS)

    async def cog_load(self):
        await self.load_blocked_users()
        self.bot.add_app_command_check(
            self.check_not_blocked,
            slash_commands=True,
            user_commands=True,
            message_commands=True,
        )

    def cog_unload(self):
        self.bot.remove_app_command_check(
            self.check_not_blocked,
            slash_commands=True,
            user_commands=True,
            message_commands=True,
        )

    async def load_blocked_users(self):
        async with RedisManager() as redis:
            records = await redis.load_many(BotBlocking, "*")
        self.blocked = {int(record.user_id): record for record in records}

    async def get_user_from_redis(self, user_id: int):
        async with RedisManager() as redis:
            return await redis.load(BotBlocking, key=str(user_id))

    @staticmethod
    def _owner_mention(guild: disnake.Guild) -> str:
        if guild.owner:
            return guild.owner.mention
        if guild.owner_id:
            return f"<@{guild.owner_id}>"
        return "командования"

    @staticmethod
    def _slot_filled(value) -> bool:
        return value not in (MISSING, None, "")

    def _get_reason(self, record: BotBlocking) -> dict | None:
        description = record.descriptions_blocking
        if not self._slot_filled(description):
            return None
        return {
            "description": description,
            "banned_by": record.banned_by or "неизвестно",
            "time": record.time_blocking or "неизвестно",
        }

    @staticmethod
    def _set_reason(record: BotBlocking, description: str, moderator_mention: str, timestamp: str) -> None:
        record.descriptions_blocking = description
        record.banned_by = moderator_mention
        record.time_blocking = timestamp

    @staticmethod
    def _add_reason_field(embed: disnake.Embed, reason: dict | None) -> disnake.Embed:
        if reason is None:
            embed.add_field(
                name=f"{ICON_NOTE} Причина блокировки лейтенанта",
                value="Сведения о причине не были зафиксированы в системе штаба. Соответствующая запись в журнале распоряжений отсутствует.",
                inline=False,
            )
            return embed
        embed.add_field(
            name=f"{ICON_NOTE} Причина блокировки лейтенанта",
            value=(
                f"**Причина:** {reason['description']}\n"
                f"**Заблокировал:** {reason['banned_by']}\n"
                f"**Дата:** {reason['time']}"
            ),
            inline=False,
        )
        return embed

    @staticmethod
    def _community_file() -> disnake.File:
        return disnake.File(Community_Image, filename="community.png")

    def _create_embed(self, title: str, description: str, icon: str = ICON_INFO) -> disnake.Embed:
        return disnake.Embed(
            title=f"{icon} {title}",
            description=description,
            color=self.embed_color,
        )

    async def _send_ban_notice(self, user: disnake.User, record: BotBlocking, owner_mention: str) -> bool:
        reason = self._get_reason(record)
        reason_text = reason["description"] if reason else "не указана"
        embed = self._create_embed(
            "Допуск к системе Game Quest ограничен",
            (
                f"> {RANK} {user.mention}. Ваш доступ к системам штаба приостановлен приказом командования. "
                "Сообщения в служебных каналах будут удаляться автоматически.\n\n"
                f"**Причина блокировки:** {reason_text}\n"
                f"**По вопросам восстановления:** {owner_mention}"
            ),
        )
        embed.set_image(url="attachment://community.png")
        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
        try:
            await user.send(
                embed=embed,
                file=self._community_file(),
                delete_after=NOTICE_INTERVAL.total_seconds(),
            )
            return True
        except disnake.HTTPException:
            return False

    async def check_not_blocked(self, inter: disnake.ApplicationCommandInteraction) -> bool:
        if not inter.guild or inter.author.id not in self.blocked:
            return True
        owner = self._owner_mention(inter.guild)
        await inter.response.send_message(embed=no_access_embed(self.embed_color, owner), ephemeral=True)
        return False

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot or not message.guild:
            return
        if message.author.id not in self.blocked:
            return
        try:
            await message.delete()
        except disnake.HTTPException:
            pass

        record = await self.get_user_from_redis(message.author.id)
        if record is None:
            self.blocked.pop(message.author.id, None)
            return

        now = current_time()
        last_notice = record.last_pm_at if self._slot_filled(record.last_pm_at) else None
        should_notify = True
        if last_notice is not None:
            try:
                should_notify = (
                    datetime.strptime(now, "%d.%m.%Y %H:%M:%S")
                    - datetime.strptime(last_notice, "%d.%m.%Y %H:%M:%S")
                ) >= NOTICE_INTERVAL
            except ValueError:
                pass
        if not should_notify:
            self.blocked[message.author.id] = record
            return

        await self._send_ban_notice(message.author, record, self._owner_mention(message.guild))
        record.last_pm_at = now
        self.blocked[message.author.id] = record
        async with RedisManager() as redis:
            await redis.save(record, key=str(message.author.id))

    @commands.slash_command(name="block", description="Управление реестром лиц, лишённых допуска к системе штаба")
    @commands.default_member_permissions(moderate_members=True, administrator=True)
    async def botban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(name="пользователь", description="Укажите пользователя"),
        action: str = commands.Param(name="действие", description="Выберите действие", choices=["забанить", "разбанить", "посмотреть"]),
        reason: str = commands.Param(name="причина", description="Основание для блокировки", default=""),
    ):
        if not inter.guild:
            await inter.response.send_message("Команда доступна только на сервере.", ephemeral=True)
            return

        owner = self._owner_mention(inter.guild)
        admins_mentions = " ".join(f"<@{user_id}>" for user_id in ALLOWED_USER_IDS)
        if not any(role.id in self.moder_ids for role in inter.author.roles):
            await inter.response.send_message(embed=no_access_embed(self.embed_color, owner), ephemeral=True)
            return

        if user.bot or user.id == inter.author.id:
            await inter.response.send_message(embed=invalid_input_embed(self.embed_color, admins_mentions), ephemeral=True)
            return
        if user.id in self.allowed_users or user.id in self.moder_ids:
            await inter.response.send_message(embed=security_block_embed(self.embed_color, owner), ephemeral=True)
            return

        await inter.response.defer(ephemeral=True)

        if action == "посмотреть":
            await self._handle_view(inter, user)
            return
        if action == "забанить":
            await self._handle_ban(inter, user, reason, admins_mentions)
            return
        await self._handle_unban(inter, user)

    async def _handle_view(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User) -> None:
        record = await self.get_user_from_redis(user.id)
        if record is None:
            embed = self._create_embed(
                f"Личное дело {user.name}",
                f"> {RANK} {user.mention} не числится в реестре неблагонадёжных лиц. Сведения о нарушениях или ограничениях доступа в отношении данного военнослужащего в системе не зарегистрированы.",
            )
            await inter.followup.send(embed=embed, ephemeral=True)
            return

        last_notice = record.last_pm_at if self._slot_filled(record.last_pm_at) else "не отправлялось"
        embed = self._create_embed(
            f"Личное дело {user.name}",
            (
                f"> {RANK} {user.mention} официально числится в реестре неблагонадёжных лиц. "
                "Информация о включении в данный список подтверждена системой штаба. "
                "Действующий статус сохраняется до особого распоряжения командования."
            ),
        )
        self._add_reason_field(embed, self._get_reason(record))
        embed.add_field(name=f"{ICON_NOTIFICATION} Последнее уведомление о блокировке", value=last_notice, inline=False)
        await inter.followup.send(embed=embed, ephemeral=True)

    async def _handle_ban(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User,
        reason: str,
        admins_mentions: str,
    ) -> None:
        if not reason.strip():
            await inter.followup.send(embed=invalid_input_embed(self.embed_color, admins_mentions), ephemeral=True)
            return

        existing_record = await self.get_user_from_redis(user.id)
        if existing_record is not None:
            embed = self._create_embed(
                "Распоряжение уже действует",
                f"> {RANK} {user.mention} уже находится в реестре неблагонадёжных лиц штаба. Повторное внесение сведений не требуется, так как соответствующая запись уже зарегистрирована в системе.",
            )
            self._add_reason_field(embed, self._get_reason(existing_record))
            await inter.followup.send(embed=embed, ephemeral=True)
            return

        record = BotBlocking(user_id=str(user.id), username=user.name, last_pm_at=None)
        self._set_reason(record, reason.strip(), inter.author.mention, current_time())
        async with RedisManager() as redis:
            await redis.save(record, key=str(user.id))
        self.blocked[user.id] = record

        embed = self._create_embed(
            "Распоряжение о блокировке подписано",
            f"> {RANK} {user.mention} лишён допуска к внутренним системам штаба до особого распоряжения командования.",
            icon=ICON_BAN,
        )
        self._add_reason_field(embed, self._get_reason(record))
        await inter.followup.send(embed=embed, ephemeral=True)

    async def _handle_unban(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User) -> None:
        record = await self.get_user_from_redis(user.id)
        reason_before = self._get_reason(record) if record else None

        async with RedisManager() as redis:
            await redis.delete(BotBlocking, key=str(user.id))
        self.blocked.pop(user.id, None)

        embed = self._create_embed(
            "Распоряжение о восстановлении допуска подписано",
            f"> {RANK} {user.mention} восстановлен в полном объёме прав доступа к внутренним системам штаба. Ограничения сняты, служебные полномочия восстановлены.",
            icon=ICON_UNBAN,
        )
        self._add_reason_field(embed, reason_before)
        await inter.followup.send(embed=embed, ephemeral=True)
