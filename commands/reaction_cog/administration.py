import disnake
from disnake.ext import commands
import asyncio

from BANNED_FILES.config import REACTION_CATEGORY_IDS, GROUP_ADMIN_ID, Admin_Reaction

class ReactionAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return

        # Проверка категории
        category_id = getattr(message.channel, "category_id", None)
        if category_id not in REACTION_CATEGORY_IDS:
            return

        # Проверка роли
        if not any(role.id in GROUP_ADMIN_ID for role in getattr(message.author, "roles", [])):
            return

        asyncio.create_task(self._process_message(message))

    async def _process_message(self, message: disnake.Message):
        await asyncio.sleep(10)
        try:
            await message.clear_reactions()

            for emoji_id in Admin_Reaction:
                emoji = self.bot.get_emoji(emoji_id)
                if emoji:
                    await message.add_reaction(emoji)
                else:
                    print(f"[ReactionAdmin] Эмодзи с ID {emoji_id} не найден.")

        except disnake.Forbidden:
            pass
        except disnake.NotFound:
            pass
        except Exception as e:
            print(f"[ReactionAdmin] Ошибка: {e}")

