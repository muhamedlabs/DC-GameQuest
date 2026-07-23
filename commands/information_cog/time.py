import disnake
from datetime import datetime, timedelta
from BANNED_FILES.config import Time_interval

moscow_time = (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")

kyiv_time = (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")

hours_time = (datetime.utcnow() + timedelta(hours=Time_interval)).strftime("%d.%m.%Y %H:%M:%S")



def current_time() -> str:
    return (datetime.utcnow() + timedelta(hours=Time_interval)).strftime("%d.%m.%Y %H:%M:%S")