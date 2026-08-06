import asyncio
import datetime

import disnake
from disnake.errors import Forbidden, NotFound
from disnake.ext import commands

from BANNED_FILES.config import ALLOWED_USER_IDS, Embed_Color, GROUP_MODER_IDS, Message_Cleaning
from commands.information_cog.time import hours_time
from commands.information_cog.warnings import no_access_embed


class CleanCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.command(name="за", help="Зачистка канала связи")
    async def purge_channel(self, ctx: commands.Context):

        if not any(role.id in GROUP_MODER_IDS for role in ctx.author.roles):
            
            owner = ctx.guild.owner.mention if ctx.guild and ctx.guild.owner else "Нет владельца"
            admins_mentions = " ".join(f"<@{user_id}>" for user_id in ALLOWED_USER_IDS)

            embed = no_access_embed(self.embed_color, owner, admins_mentions)

            try:
                message = await ctx.send(embed=embed)
                await asyncio.sleep(7)

                try:
                    await message.delete()
                except NotFound:
                    pass

            except Forbidden:
                print("[CleanCommand] Нет прав отправить embed")

            return

        deleted_count = 0

        try:
            fourteen_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14)

            try:
                deleted = await ctx.channel.purge(
                    limit=Message_Cleaning,
                    after=fourteen_days_ago,
                    bulk=True,
                )
                deleted_count += len(deleted)
            except Forbidden:
                print("[CleanCommand] Нет прав на bulk-удаление")
            except Exception as error:
                print(f"[CleanCommand] Ошибка bulk-удаления: {error}")

            remaining_limit = Message_Cleaning - deleted_count
            if remaining_limit > 0:
                async for message in ctx.channel.history(limit=remaining_limit, before=fourteen_days_ago):
                    try:
                        await message.delete()
                        deleted_count += 1
                        await asyncio.sleep(1)

                    except NotFound:
                        continue

                    except Forbidden:
                        continue

                    except Exception as error:
                        print(f"[CleanCommand] Ошибка удаления сообщения: {error}")

            embed = disnake.Embed(
                title="<:infocircle:1390374048650760324> Доклад о выполненной очистке канала связи",
                description=(
                    f"Согласно оперативному распоряжению командования, проведена полная нейтрализация информационного шума.\n\n"
                    f"<:trash:1487340036453171270> **Удалено сообщений в канале:**\n ```{deleted_count}```\n"
                    f"<:calendar:1390972430780203058> **Время доклада:** {hours_time} по МСК"
                ),
                color=self.embed_color,
            )

            try:
                message = await ctx.send(embed=embed)
                await asyncio.sleep(15)

                try:
                    await message.delete()
                except NotFound:
                    pass

            except Forbidden:
                print("[CleanCommand] Нет прав отправить embed")

        except Exception as error:
            try:
                await ctx.send(f"Ошибка при выполнении операции: {error}")
            except Exception:
                pass
