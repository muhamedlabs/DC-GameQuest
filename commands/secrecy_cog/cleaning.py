import disnake
from disnake.ext import commands
import asyncio
from datetime import datetime, timedelta
from BANNED_FILES.config import Embed_Color, Message_Cleaning, ALLOWED_USER_IDS

class CleanCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.command(name="зачистка", help="Зачистка канала связи")
    @commands.has_permissions(manage_messages=True)
    async def purge_channel(self, ctx: commands.Context):
        if ctx.author.id not in ALLOWED_USER_IDS:
            return

        try:
            deleted_count = 0
            async for msg in ctx.channel.history(limit=Message_Cleaning):
                try:
                    await msg.delete()
                    deleted_count += 1
                    await asyncio.sleep(0.8)  # задержка между удалениями
                except disnake.Forbidden:
                    continue  # нет прав на удаление этого сообщения
                except Exception as e:
                    print(f"[CleanCommand] Ошибка удаления сообщения: {e}")

            moscow_time = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")

            embed = disnake.Embed(
                title="<:infocircle:1390374048650760324>  Доклад о выполненной очистке канала связи",
                description=(
                    f"```Согласно оперативному распоряжению командования, проведена полная нейтрализация информационного шума. "
                    f"Удалено сообщений: {deleted_count}```\n"
                    f"<:calendar:1390972430780203058> **Время доклада:** {moscow_time} по МСК"
                ),
                color=self.embed_color
            )

            msg = await ctx.send(embed=embed)
            await asyncio.sleep(15)
            await msg.delete()

        except Exception as e:
            await ctx.send(f"⚠️ Ошибка при выполнении операции: {e}")
