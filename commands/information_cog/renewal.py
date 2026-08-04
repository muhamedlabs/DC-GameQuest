import aiohttp
import disnake
from disnake.ext import commands
from datetime import datetime

from BANNED_FILES.config import Embed_Color, RedisManager, GITHUB_OWNER_BOT, GITHUB_REPO_BOT
from redis_storage.bot_information import BotInformation


class Updates(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))

    @commands.Cog.listener()
    async def on_ready(self):
        key = [str(self.bot.user.id)]

        async with RedisManager() as redis:
            bot_info = await redis.load(BotInformation, key)

            if bot_info is None:
                bot_info = BotInformation(bot_id=str(self.bot.user.id))
                current = 0
            else:
                try:
                    current = int(round(float(bot_info.version) * 100)) if bot_info.version not in (None, "") else 0
                except (TypeError, ValueError):
                    current = 0

            current += 1
            bot_info.version = f"{current / 100:.2f}"

            await redis.save(bot_info, key)

    async def get_version_str(self) -> str:
        key = [str(self.bot.user.id)]
        async with RedisManager() as redis:
            bot_info = await redis.load(BotInformation, key)
            if bot_info is None or not bot_info.version:
                return "0.00"
            return bot_info.version

    @commands.slash_command(name="обновления", description="Развитие и обновления сержанта Game Quest")
    async def updates(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()

        url = f"https://api.github.com/repos/{GITHUB_OWNER_BOT}/{GITHUB_REPO_BOT}/commits?per_page=3"
        headers = {"Accept": "application/vnd.github+json"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    await inter.edit_original_response(
                        content=f"Ошибка запроса к GitHub API: {resp.status}"
                    )
                    return
                commits = await resp.json()

        version = await self.get_version_str()

        embed = disnake.Embed(
            title=f"<:cpucharge:1534270497171312663> Боевые обновления сержанта — v{version}",
            description=">>> Штаб фиксирует последние изменения в системе. Полный отчёт о проведённых операциях, устранённых неполадках и новых рубежах бота.",
            color=self.embed_color,
        )

        for commit in commits:
            message = commit["commit"]["message"].split("\n")[0]
            author = commit["commit"]["author"]["name"]
            commit_url = commit["html_url"]
            raw_date = commit["commit"]["author"]["date"][:10]
            date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d.%m.%Y")

            embed.add_field(
                name=f"{message}",
                value=f"<:ram:1534270499490758676> **Отчёт об операции**: [GitHub]({commit_url})\n<:userhexagon:1391013148592443463> **Командир:** {author}\n <:calendar:1390972430780203058> **Дата операции:** {date}",
                inline=False,
            )

        await inter.edit_original_response(embed=embed)
