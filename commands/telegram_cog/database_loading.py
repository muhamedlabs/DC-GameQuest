from typing import List, Optional
from datetime import datetime, timedelta
from redis_storage.social_connections import SocialConnections
from BANNED_FILES.config import RedisManager
from pytz import timezone


class RedisMessageMapper:
    def __init__(self, bot, message_lifetime_hours: int = 24):
        self.message_lifetime = timedelta(hours=message_lifetime_hours)
        self.redis = RedisManager()
        self.moscow_tz = timezone("Europe/Moscow")
        self.bot = bot

    async def add_message_mapping(
        self,
        telegram_message_ids: List[int],
        discord_message_id: int,
        telegram_texts: Optional[List[str]] = None,
    ):
        if not telegram_message_ids:
            return

        current_time = datetime.now(self.moscow_tz).isoformat()

        try:
            async with self.redis:
                for i, tg_id in enumerate(telegram_message_ids):
                    preview = ""
                    if telegram_texts and i < len(telegram_texts):
                        preview = " ".join(telegram_texts[i].split()[:2])
                    key = [f"{discord_message_id}:{tg_id}"]
                    mapping = SocialConnections(
                        telegram_message_id=tg_id,
                        discord_message_id=discord_message_id,
                        timestamp=current_time,
                        message_preview=preview,
                    )
                    await self.redis.save(mapping, key, ttl=self.message_lifetime)
        except Exception:
            raise

    async def get_message_mapping(self, discord_message_id: int, telegram_message_id: int) -> Optional[SocialConnections]:
        key = [f"{discord_message_id}:{telegram_message_id}"]
        try:
            async with self.redis:
                return await self.redis.load(SocialConnections, key)
        except Exception:
            return None

    # Изменённый метод для удаления по telegram_message_id, возвращающий discord_message_id
    async def remove_message_mapping(self, telegram_message_id: int) -> Optional[int]:
        try:
            async with self.redis:
                all_mappings = await self.redis.load_many(SocialConnections, key="*")
                for mapping in all_mappings:
                    if mapping and mapping.telegram_message_id == telegram_message_id:
                        key = [f"{mapping.discord_message_id}:{mapping.telegram_message_id}"]
                        await self.redis.delete(SocialConnections, key)
                        return mapping.discord_message_id
        except Exception:
            return None
        return None

    async def has_message_mapping(self, discord_message_id: int, telegram_message_id: int) -> bool:
        key = [f"{discord_message_id}:{telegram_message_id}"]
        try:
            async with self.redis:
                mapping = await self.redis.load(SocialConnections, key)
                return mapping is not None
        except Exception:
            return False

    async def get_all_telegram_ids_for_discord(self, discord_message_id: int) -> List[int]:
        try:
            async with self.redis:
                all_mappings = await self.redis.load_many(SocialConnections, key="*")
                return [
                    m.telegram_message_id for m in all_mappings
                    if m and m.discord_message_id == discord_message_id
                ]
        except Exception:
            return []

    async def get_all_discord_ids_for_telegram(self, telegram_message_id: int) -> List[int]:
        try:
            async with self.redis:
                all_mappings = await self.redis.load_many(SocialConnections, key="*")
                return [
                    m.discord_message_id for m in all_mappings
                    if m and m.telegram_message_id == telegram_message_id
                ]
        except Exception:
            return []

    async def clear_all_mappings(self):
        try:
            async with self.redis:
                all_mappings = await self.redis.load_many(SocialConnections, key="*")
                for mapping in all_mappings:
                    if mapping:
                        key = [f"{mapping.discord_message_id}:{mapping.telegram_message_id}"]
                        await self.redis.delete(SocialConnections, key)
        except Exception:
            pass

    async def get_mappings_count(self) -> int:
        try:
            async with self.redis:
                all_mappings = await self.redis.load_many(SocialConnections, key="*")
                return len([m for m in all_mappings if m])
        except Exception:
            return 0

    async def get_discord_message_id(self, telegram_message_id: int) -> Optional[int]:
        try:
            async with self.redis:
                all_mappings = await self.redis.load_many(SocialConnections, key="*")
                for mapping in all_mappings:
                    if mapping and mapping.telegram_message_id == telegram_message_id:
                        return mapping.discord_message_id
        except Exception:
            pass
        return None

    async def get_message_preview(self, telegram_message_id: int) -> Optional[str]:
        try:
            async with self.redis:
                all_mappings = await self.redis.load_many(SocialConnections, key="*")
                for mapping in all_mappings:
                    if mapping and mapping.telegram_message_id == telegram_message_id:
                        return mapping.message_preview
        except Exception:
            pass
        return None
