import asyncio
import discord
from discord.ext import commands
import os

# Use environment variable for bot token
TOKEN = os.getenv("DISCORD_TOKEN")

# Full intents (adjust if you don’t need everything)
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

    if TOKEN:
        await bot.start(TOKEN)
    else:
        print("❌ No bot token found. Please set DISCORD_TOKEN as an environment variable.")

@bot.event
async def on_ready():
    """Triggered when bot is online."""
    print(f"✅ Jeeves has risen. Logged in as {bot.user.name}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global commands:")
        for cmd in synced:
            print(f"- /{cmd.name}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

if __name__ == "__main__":
    asyncio.run(main())
