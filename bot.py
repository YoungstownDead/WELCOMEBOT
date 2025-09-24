import asyncio
import discord
from discord.ext import commands
import os

# Reads the bot token from a local INFO.txt file
script_dir = os.path.dirname(os.path.abspath(__file__))
INFO_FILE = os.path.join(script_dir, "INFO.txt")

def read_token():
    """Reads bot token from INFO.txt"""
    try:
        with open(INFO_FILE, "r", encoding="utf-8") as file:
            return file.read().strip()
    except IOError as e:
        print(f"Error reading token file: {e}")
        return None

intents = discord.Intents.all()

# Uses mention as prefix, but primarily relies on slash commands
bot = commands.Bot(command_prefix=commands.when_mentioned, intents=intents)

async def main():
    """Loads all bot cogs and starts the bot."""
    cogs_to_load = (
        "cogs.events",
        "cogs.commands",
        "cogs.music",
        "cogs.modal_achievements",
        "cogs.creepy_images"  # <-- Ensuring creepy images cog is included
    )

    for extension in cogs_to_load:
        try:
            await bot.load_extension(extension)
            print(f"{extension} loaded.")
        except Exception as e:
            print(f"Error loading {extension}: {e}")

    token = read_token()
    if token:
        await bot.start(token)
    else:
        print("Bot token not found. Please check INFO.txt.")

@bot.event
async def on_ready():
    """Triggered when bot is online."""
    print(f"Logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} global commands:")
        for cmd in synced:
            print(f"- /{cmd.name}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

if __name__ == "__main__":
    asyncio.run(main())
