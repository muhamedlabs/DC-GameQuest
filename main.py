import disnake
import os
import datetime
import ashredis 
from dotenv import load_dotenv
from disnake.ext import commands
from BANNED_FILES.config import discord_bot

# Загрузка переменных окружения
load_dotenv()

# Настройка intents
intents = disnake.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True
intents.guilds = True

# Инициализация бота
bot = commands.Bot(command_prefix="!", intents=intents)

bot.start_time = datetime.datetime.utcnow()

# Событие при запуске
@bot.event
async def on_ready():
    print(f"Bot {bot.user} is up and running!")

# Загружаем коги
bot.load_extension("commands.status_cog") # Папка статус

bot.load_extension("commands.speaker_cog") # Папка спикер

bot.load_extension("commands.design_cog") # Папка с дизайном профилей дискорда

bot.load_extension("commands.telegram_cog") # Папка с подключения постинга из Telegram

bot.load_extension("commands.messages_cog") # Папка с сообщениями от бота

bot.load_extension("commands.ember_cog") # Папка с ембитам для отправки

bot.load_extension("commands.events_cog") # Папка с событиями на сервере и боте

bot.load_extension("commands.reaction_cog") # Папка с рекциями на сообщения

bot.load_extension("commands.moderation_cog") # Папка с модерацией на сервере и в боте

bot.load_extension("commands.information_cog") # Папка с информация о сервере

bot.load_extension("commands.secrecy_cog") # Папка с секретными командами через !

bot.load_extension("commands.primary_cog") # Папка с особо-основными действиями бота

bot.load_extension("commands.database_cog.models") # Папка с выгрузкой из Redis


# Запуск
if __name__ == "__main__":
    bot.run(discord_bot)
