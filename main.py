import disnake
import os
import datetime
from dotenv import load_dotenv
from disnake.ext import commands
from BANNED_FILES.config import discord_bot

load_dotenv()

intents = disnake.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
intents.presences = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

bot.start_time = datetime.datetime.utcnow()

@bot.event
async def on_ready():
    print(f"Bot {bot.user} is up and running!")

bot.load_extension("commands.status_cog")
bot.load_extension("commands.speaker_cog")
bot.load_extension("commands.design_cog")
bot.load_extension("commands.telegram_cog")
bot.load_extension("commands.messages_cog")
bot.load_extension("commands.ember_cog")
bot.load_extension("commands.events_cog")
bot.load_extension("commands.reaction_cog")
bot.load_extension("commands.moderation_cog")
bot.load_extension("commands.information_cog")
bot.load_extension("commands.secrecy_cog")
bot.load_extension("commands.primary_cog")

if __name__ == "__main__":
    bot.run(discord_bot)
