import disnake
from disnake.ext import commands
import os
from BANNED_FILES.config import Embed_Color, Reboot_Gif, GROUP_ADMIN_ID, IGNORED_RELOAD_DIRS

class ReloadAllCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.slash_command(
        name="bot_restart",
        description="Обновление конфигурации сержанта",
        dm_permission=False,
        default_member_permissions=disnake.Permissions(manage_guild=True)
    )
    async def reload_all(self, inter: disnake.AppCmdInter):
        # Проверка доступа
        has_access = (
            any(role.id in GROUP_ADMIN_ID for role in inter.author.roles)
            if isinstance(GROUP_ADMIN_ID, list)
            else any(role.id == GROUP_ADMIN_ID for role in inter.author.roles)
        )

        if not has_access:
            embed = disnake.Embed(
                title="<:forbidden:1390972224436965386> Доступ к команде заблокирован",
                description=(
                    "У вас **отсутствуют полномочия** для выполнения данного приказа.\n\n"
                    ">>> Если вы считаете, что это ошибка — немедленно свяжитесь с адмиралом базы: "
                    f"{inter.guild.owner.mention}"
                ),
                color=self.embed_color
            )
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        await inter.response.defer(ephemeral=True)

        base_dir = os.path.join(os.getcwd(), "commands")
        errors = []
        success = []
        skipped = []

        gif_path = Reboot_Gif
        gif_attached = os.path.exists(gif_path)
        file = disnake.File(gif_path, filename="reload.gif") if gif_attached else None

        for entry in os.listdir(base_dir):
            if entry in IGNORED_RELOAD_DIRS:
                skipped.append(f"`{entry}`")
                continue

            path = os.path.join(base_dir, entry)
            if os.path.isdir(path):
                cog_name = f"commands.{entry}"
                try:
                    if cog_name in self.bot.extensions:
                        self.bot.reload_extension(cog_name)
                    else:
                        self.bot.load_extension(cog_name)
                    success.append(f"`{entry}`")
                except Exception as e:
                    errors.append(f"`{entry}` — `{e}`")

        embed = disnake.Embed(
            title="<:cloudchange:1388950504297726113> Тактическая перезагрузка завершена",
            description=(
                ">>> По данным, состояние боевых когов оценивается как **стабильно напряжённое**. "
                "Наблюдается планомерное выполнение поставленных **задач** при сохранении постоянной боеготовности."
            ),
            color=self.embed_color
        )

        if success:
            embed.add_field(
                name="<:chartsuccess:1388950545733124106> Успешно восстановлены:",
                value="\n".join(success),
                inline=False
            )

        if skipped:
            embed.add_field(
                name="<:health:1398745774036094996> Пропущены (игнор):",
                value="\n".join(skipped),
                inline=False
            )

        if errors:
            embed.add_field(
                name="<:chartfail:1388950527165075517> Обнаружены сбои:",
                value="\n".join(errors),
                inline=False
            )

        embed.set_footer(text="Благодарим за проявленный интерес к нашему спецпроекту!")
        if gif_attached:
            embed.set_image(url="attachment://reload.gif")

        await inter.edit_original_response(embed=embed, file=file if gif_attached else None)
