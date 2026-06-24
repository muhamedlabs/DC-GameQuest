import disnake
from disnake.ext import commands
import asyncio
import datetime
from disnake.errors import NotFound, Forbidden
from commands.information_cog.time import time
from commands.information_cog.warnings import no_access_embed
from BANNED_FILES.config import Embed_Color, Message_Cleaning, ALLOWED_USER_IDS


class CleanCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.command(name="за", help="Зачистка канала связи")
    async def purge_channel(self, ctx: commands.Context):

        if ctx.author.id not in ALLOWED_USER_IDS:

            owner = ctx.guild.owner.mention if ctx.guild and ctx.guild.owner else "Нет владельца"
            admins_mentions = " ".join(f"<@{uid}>" for uid in ALLOWED_USER_IDS)

            embed = no_access_embed(self.embed_color, owner, admins_mentions)

            try:
                msg = await ctx.send(embed=embed)
                await asyncio.sleep(7)

                try:
                    await msg.delete()
                except NotFound:
                    pass

            except Forbidden:
                print("[CleanCommand] Нет прав отправить embed")

            return

        deleted_count = 0

        try:
            # bulk delete для сообщений младше 14 дней (быстро, мало рейт-лимитов)
            fourteen_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14)

            try:
                deleted = await ctx.channel.purge(
                    limit=Message_Cleaning,
                    after=fourteen_days_ago,
                    bulk=True
                )
                deleted_count += len(deleted)
            except Forbidden:
                print("[CleanCommand] Нет прав на bulk-удаление")
            except Exception as e:
                print(f"[CleanCommand] Ошибка bulk-удаления: {e}")

            # отдельно добиваем старые сообщения (>14 дней), их purge bulk не берёт
            remaining_limit = Message_Cleaning - deleted_count
            if remaining_limit > 0:
                async for msg in ctx.channel.history(limit=remaining_limit, before=fourteen_days_ago):
                    try:
                        await msg.delete()
                        deleted_count += 1
                        await asyncio.sleep(1)  # старые сообщения удаляются по одному, лимит жёстче

                    except NotFound:
                        continue

                    except Forbidden:
                        continue

                    except Exception as e:
                        print(f"[CleanCommand] Ошибка удаления сообщения: {e}")

            embed = disnake.Embed(
                title="<:infocircle:1390374048650760324> Доклад о выполненной очистке канала связи",
                description=(
                    f"Согласно оперативному распоряжению командования, проведена полная нейтрализация информационного шума.\n\n"
                    f"<:trash:1487340036453171270> **Удалено сообщений в канале:**\n ```{deleted_count}```\n"
                    f"<:calendar:1390972430780203058> **Время доклада:** {time} по МСК"
                ),
                color=self.embed_color
            )

            try:
                msg = await ctx.send(embed=embed)
                await asyncio.sleep(15)

                try:
                    await msg.delete()
                except NotFound:
                    pass

            except Forbidden:
                print("[CleanCommand] Нет прав отправить embed")

        except Exception as e:
            try:
                await ctx.send(f"Ошибка при выполнении операции: {e}")
            except Exception:
                pass