import os
import random
import json
import discord
from discord.ext import commands

from utils.gpt_client import DEFAULT_SYSTEM_PROMPT, gpt_is_configured, request_chat_completion

# ----- File Paths ----- 
# Change DATA_FOLDER to "welcomedata" if your welcome assets live there.
script_dir = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(script_dir, "..", "welcomedata")

FAREWELL_MESSAGES_FILE = os.path.join(DATA_FOLDER, "farewell.txt")
DEFAULT_AVATAR_FILENAME = os.path.join(DATA_FOLDER, "default.png")
AVATARS_DIR = os.path.join(DATA_FOLDER, "Avatars")
DATA_FILE = os.path.join(DATA_FOLDER, "message_counts.json")
USER_TRACK_FILE = os.path.join(DATA_FOLDER, "user_progression.json")

# ----- Guild & Role Settings -----
PRIMARY_GUILD_ID = 938304756185710642     # Replace with your guild's ID
WELCOME_CHANNEL_ID = 938304756185710645    # Replace with your welcome channel ID
FAREWELL_CHANNEL_ID = 938304756185710645    # Replace with your farewell channel ID
DEFAULT_ROLE_ID = 1121956519534133449         # Replace with your default role ID

ROLE_THRESHOLDS = {
    1:    "Mildly Interesting",
    10:   "Infinite Curiosity",
    25:   "Glitch in the Matrix",
    50:   "Error 404",
    95:   "Quantum Observer",
    100:  "Reality Distortion Specialist",
    125:  "Persistent Error",
    150:  "Unstable Element",
    200:  "Time Loop Survivor",
    245:  "Cosmic Anomaly",
    388:  "Lab Rat Extraordinaire",
    500:  "Chaotic Singularity",
    608:  "Temporal Rift Connoisseur",
    783:  "Dimension Shifter",
    800:  "Breaks the Simulation",
    900:  "Cosmic Archon",
    1030: "Anomaly Overlord",
    1230: "Infinite Loop",
    1500: "Grand Archivist",
    2000: "Godlike Algorithm"
}

# ----- Helper Functions -----
def read_messages(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            return [line.strip() for line in file if line.strip()]
    except IOError as e:
        print(f"Error reading messages from {file_path}: {e}")
        return []

def load_data(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.decoder.JSONDecodeError:
        return {}

def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# ----- Preload Data -----
farewell_messages = read_messages(FAREWELL_MESSAGES_FILE)
os.makedirs(AVATARS_DIR, exist_ok=True)
message_counts = load_data(DATA_FILE)
user_progression = load_data(USER_TRACK_FILE)

# ----- Events Cog Class -----
class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"[Events Cog] Logged in as {self.bot.user}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Only operate in the primary guild
        if member.guild.id != PRIMARY_GUILD_ID:
            return

        welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
        if not welcome_channel:
            print(f"Welcome channel not found for guild {member.guild.id}.")
            return

        avatar_path = os.path.join(AVATARS_DIR, f"{member.name}.png")
        if member.avatar:
            # Save the member's avatar image as {username}.png
            await member.avatar.save(avatar_path)
        else:
            avatar_path = DEFAULT_AVATAR_FILENAME

        file = discord.File(avatar_path)
        await welcome_channel.send(file=file)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # Only operate in the primary guild
        if member.guild.id != PRIMARY_GUILD_ID:
            return

        farewell_channel = member.guild.get_channel(FAREWELL_CHANNEL_ID)
        if not farewell_channel:
            print(f"Farewell channel not found for guild {member.guild.id}.")
            return

        avatar_path = os.path.join(AVATARS_DIR, f"{member.name}.png")
        if not os.path.exists(avatar_path):
            avatar_path = DEFAULT_AVATAR_FILENAME

        # Choose a random farewell message, and format it with the member's name if needed
        message_text = random.choice(farewell_messages).format(filename=member.name)
        embed = discord.Embed(description=message_text, color=0xff0000)
        if self.bot.user.avatar:
            embed.set_author(name="Farewell!", icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=f"attachment://{os.path.basename(avatar_path)}")

        file = discord.File(avatar_path)
        await farewell_channel.send(embed=embed, file=file)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        await self._maybe_reply_with_gpt(message)

        if message.guild is None or message.guild.id != PRIMARY_GUILD_ID:
            await self.bot.process_commands(message)
            return

        user_id = str(message.author.id)
        if user_id not in message_counts:
            message_counts[user_id] = 0
        message_counts[user_id] += 1
        save_data(DATA_FILE, message_counts)

        user_message_count = message_counts[user_id]
        for threshold, role_name in sorted(ROLE_THRESHOLDS.items(), reverse=True):
            if user_message_count >= threshold:
                role = await self.get_or_create_role(message.guild, role_name)
                if role and role not in message.author.roles:
                    await message.author.add_roles(role)
                    await message.channel.send(f"{message.author.mention}, you have been promoted to **{role_name}**!")
                    user_progression[user_id] = role_name
                    save_data(USER_TRACK_FILE, user_progression)
                    # Remove previously assigned roles
                    for prev_threshold, prev_role_name in ROLE_THRESHOLDS.items():
                        if prev_role_name != role_name:
                            prev_role = discord.utils.get(message.guild.roles, name=prev_role_name)
                            if prev_role and prev_role in message.author.roles:
                                await message.author.remove_roles(prev_role)
                                print(f"Removed {prev_role_name} from {message.author.name}")
                    default_role = message.guild.get_role(DEFAULT_ROLE_ID)
                    if default_role and default_role in message.author.roles:
                        await message.author.remove_roles(default_role)
                        print(f"Removed default role from {message.author.name}")
                break

        await self.bot.process_commands(message)

    async def get_or_create_role(self, guild: discord.Guild, role_name: str):
        role = discord.utils.get(guild.roles, name=role_name)
        if role is None:
            try:
                role = await guild.create_role(name=role_name, reason="Auto-generated rank progression role")
                print(f"Created role: {role_name} in guild {guild.id}")
            except discord.Forbidden:
                print(f"Permission denied: Cannot create the role '{role_name}' in guild {guild.id}.")
        return role

    async def _maybe_reply_with_gpt(self, message: discord.Message) -> bool:
        """Respond with a GPT-powered message when directly addressed."""

        if message.guild is None:
            should_reply = True
        else:
            bot_user = self.bot.user
            should_reply = bool(bot_user and bot_user in message.mentions)

        if not should_reply:
            return False

        if not gpt_is_configured():
            await message.channel.send(
                "I regret to inform you that no GPT API key was configured."
            )
            return True

        prompt = message.clean_content.strip()
        if not prompt:
            prompt = "The user addressed you without providing any content."

        try:
            async with message.channel.typing():
                reply = await request_chat_completion(
                    prompt,
                    system_prompt=DEFAULT_SYSTEM_PROMPT,
                )
        except Exception as exc:
            await message.channel.send(f"I encountered a difficulty consulting GPT: {exc}")
            return True

        if not reply:
            reply = "I am afraid GPT had no response to offer."

        await message.channel.send(f"{message.author.mention} {reply}")
        return True

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
    print("Events cog loaded.")
