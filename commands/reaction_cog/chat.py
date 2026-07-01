import disnake
from disnake.ext import commands
import random

from BANNED_FILES.config import CHAT_CHANNEL_ID, Probability_Reaction, Chat_Reaction

class RandomReactor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_channel_id = CHAT_CHANNEL_ID

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if (
            message.channel.id != self.target_channel_id
            or message.author.bot
            or not message.content.strip()
        ):
            return

        if random.randint(1, 100) <= Probability_Reaction:
            try:
                emoji_id = random.choice(Chat_Reaction)
                emoji = self.bot.get_emoji(emoji_id)
                if emoji is None:
                    print(f"Эмодзи с ID {emoji_id} не найден в кэше бота")
                    return
                await message.add_reaction(emoji)
            except disnake.HTTPException as e:
                print(f"❌ Ошибка добавления реакции: {e}")
