import disnake
from disnake.ext import commands
from BANNED_FILES.config import RedisManager
from redis_storage.reaction_manager import ReactionManager

class ReactionTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: disnake.Reaction, user: disnake.User):
        try:
            # Ставим только если реакцию добавил сам бот
            if user.id != self.bot.user.id:
                return

            # Автор сообщения
            message_author = reaction.message.author
            user_id = str(message_author.id)
            username = str(message_author)

            key = [f"{user_id}"]

            async with RedisManager() as redis:
                record = await redis.load(ReactionManager, key)

                if record is None:
                    record = ReactionManager(
                        user_id=user_id,
                        username=username,
                        reaction_from_bot="1"
                    )
                else:
                    current_count = int(record.reaction_from_bot or "0")
                    record.reaction_from_bot = str(current_count + 1)
                    record.username = username  # Обновляем имя, если поменялось

                await redis.save(record, key)

        except Exception as e:
            print(f"[ReactionTracker] Ошибка: {e}")

    async def get_reaction_count(self, user_id: int) -> int:
        key = [f"{user_id}"]
        async with RedisManager() as redis:
            record = await redis.load(ReactionManager, key)
            if record and record.reaction_from_bot:
                return int(record.reaction_from_bot)
            return 0
