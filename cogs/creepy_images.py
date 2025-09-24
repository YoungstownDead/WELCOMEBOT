import discord
import aiohttp
import os
import random
import json
import asyncio
from discord.ext import commands

# Load creepy config
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config_creepy.json")

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as file:
        config = json.load(file)
else:
    config = {
        "CHANNEL_ID": 123456789012345678,
        "SAVE_FOLDER": "./saved_images",
        "TRIGGER_WORDS": [
            "watching", "forgotten", "shadow", "haunted", "alone",
            "glitch", "lost", "remember", "echo", "whisper",
            "dark", "secret", "void", "cursed", "door", "creep",
            "gone", "mirror", "figure", "eyes", "behind", "silent"
        ],
        "CREEPY_MESSAGES": [
            "You should be careful what you say...",
            "I don’t think you were supposed to see this again...",
            "Why does this keep coming back?",
            "Did you forget about this?",
            "You’re not alone.",
            "Some things don’t stay buried.",
            "It was waiting for you.",
            "You posted this before… didn't you?",
            "Are you sure you're alone right now?",
            "This was supposed to be deleted... wasn't it?"
        ]
    }
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

CHANNEL_ID = config["CHANNEL_ID"]
SAVE_FOLDER = config["SAVE_FOLDER"]
TRIGGER_WORDS = config["TRIGGER_WORDS"]
CREEPY_MESSAGES = config["CREEPY_MESSAGES"]

# Ensure folders exist
os.makedirs(SAVE_FOLDER, exist_ok=True)

class CreepyImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_message_time = None  # Track last message time

    async def setup_hook(self):
        """Starts the silence checker."""
        self.bot.loop.create_task(self.check_for_silence())

    def get_random_image(self):
        """Fetch a random image from the saved_images folder."""
        images = [os.path.join(SAVE_FOLDER, f) for f in os.listdir(SAVE_FOLDER) if f.endswith(("png", "jpg", "jpeg", "gif"))]
        return random.choice(images) if images else None

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handles creepy interactions and stores images."""
        if message.author.bot:
            return

        self.last_message_time = asyncio.get_running_loop().time()  # ✅ Fix loop error

        # Save images
        if message.channel.id == CHANNEL_ID and message.attachments:
            for attachment in message.attachments:
                if attachment.filename.endswith(("png", "jpg", "jpeg", "gif")):
                    await self.download_image(attachment)

        # Trigger creepy response if certain words are detected
        if any(word in message.content.lower() for word in TRIGGER_WORDS):
            if self.get_random_image():
                await self.send_creepy_image(message.channel)

        await self.bot.process_commands(message)

    async def download_image(self, attachment):
        """Downloads and saves images."""
        file_extension = attachment.filename.split('.')[-1]
        file_name = f"{attachment.id}.{file_extension}"
        save_path = os.path.join(SAVE_FOLDER, file_name)

        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as response:
                if response.status == 200:
                    with open(save_path, "wb") as file:
                        file.write(await response.read())
                    print(f"Saved image {file_name}")

    async def send_creepy_image(self, channel):
        """Sends a creepy message with an old image."""
        creepy_message = random.choice(CREEPY_MESSAGES)
        random_image = self.get_random_image()
        if random_image:
            file = discord.File(random_image)
            await channel.send(creepy_message, file=file)

    async def check_for_silence(self):
        """Sends a creepy message if there's long silence."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if self.last_message_time:
                elapsed_time = asyncio.get_running_loop().time() - self.last_message_time
                random_silence_time = random.randint(2 * 3600, 8 * 3600)  # Between 2-8 hours
                if elapsed_time > random_silence_time:
                    channel = self.bot.get_channel(CHANNEL_ID)
                    if channel and self.get_random_image():
                        await self.send_creepy_image(channel)
                    self.last_message_time = asyncio.get_running_loop().time()  # Reset timer
            await asyncio.sleep(600)  # Check every 10 minutes

async def setup(bot):
    await bot.add_cog(CreepyImageCog(bot))
