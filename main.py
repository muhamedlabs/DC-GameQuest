import disnake
import os
import datetime
import logging
import warnings
import ashredis
from dotenv import load_dotenv
from disnake.ext import commands
from BANNED_FILES.config import discord_bot, TESTING
from commands.information_cog.time import start_time_updater

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger(__name__)

# Настройка intents
intents = disnake.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True
intents.guilds = True

# Определяем Demo  если есть хотя б одина гильдия или глобально None
Demo = TESTING or None

# Инициализация бота
bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True, test_guilds=Demo)

bot.start_time = datetime.datetime.now(datetime.timezone.utc)


# Событие при запуске
@bot.event
async def on_ready():
    start_time_updater()
    print(f"Bot {bot.user} is up and running!")


# Глобальный обработчик ошибок слэш-команд
@bot.event
async def on_slash_command_error(inter: disnake.ApplicationCommandInteraction, error: commands.CommandError):
    if isinstance(error, commands.CheckFailure):
        return

    logger.exception(
        "Ошибка в слэш-команде %s", inter.application_command.name, exc_info=error
    )

# Глобальный обработчик ошибок текстовых команд (через !)
@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CheckFailure):
        return
    if isinstance(error, commands.CommandNotFound):
        return

    logger.exception("Ошибка в текстовой команде %s", ctx.command, exc_info=error)


# Загружаем коги
bot.load_extension("commands.status_cog") # Папка статус для бота(Переименовать)

bot.load_extension("commands.speaker_cog") # Папка с войс-спикер бот

bot.load_extension("commands.design_cog") # Папка с дизайном профилей дискорда

#bot.load_extension("commands.telegram_cog") # Папка с подключения постинга из Telegram

bot.load_extension("commands.advertisement_cog") # Папка с саморекламой от бота

bot.load_extension("commands.messages_cog") # Папка с сообщениями от бота

bot.load_extension("commands.dm_cog") # Папка с личными сообщениями от бота

bot.load_extension("commands.dispatcher_cog") # Папка с отправленными ембиту и другими материалами от бота

bot.load_extension("commands.postulate_cog") # Папка с постулатами и законами от бота

bot.load_extension("commands.events_cog") # Папка с событиями на сервере и боте

bot.load_extension("commands.reaction_cog") # Папка с рекциями на сообщения

bot.load_extension("commands.moderation_cog") # Папка с модерацией на сервере и в боте

bot.load_extension("commands.information_cog") # Папка с информация о сервере

bot.load_extension("commands.secrecy_cog") # Папка с секретными командами через !

bot.load_extension("commands.respond_cog") # Папка с ответами и пингом от бота

bot.load_extension("commands.database_cog") # Папка с выгрузкой из Redis файли

bot.load_extension("commands.button_cog") # Папка с кнопками по айдишке для бота

bot.load_extension("commands.broadcast_cog") # Папка с голосовыми командами под контролем бота

bot.load_extension("commands.entertainment_cog") # Папка с контентом для досуга пользователей

bot.load_extension("commands.alerts_cog") # Папка с оповещениями новостях от бота

bot.load_extension("commands.test_cog") # Папка с тестами


# Запуск
if __name__ == "__main__":
    bot.run(discord_bot)
