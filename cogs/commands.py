import discord
from discord import app_commands
from discord.ext import commands
import os
import datetime
import random
import json
import asyncio
from typing import Optional
import requests  # For API calls

# -------------------------------
# Global API Variables
# -------------------------------
NEWS_API_KEY = "045191fa787646b08895bd97cbd55e08"
SCIENCE_NEWS_BASE_URL = "https://newsapi.org/v2/top-headlines?category=science&language=en"

# -------------------------------
# Global Variable for News History File
# -------------------------------
NEWS_HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "news_history.json")


def load_news_history():
    if not os.path.isfile(NEWS_HISTORY_FILE):
        return {}
    try:
        with open(NEWS_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_news_history(history):
    with open(NEWS_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

# -------------------------------
# Helper function to save JSON data
# -------------------------------
def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# -------------------------------
# Helper function to safely send messages
# -------------------------------
async def safe_send(interaction: discord.Interaction, **kwargs):
    """Send a Discord response regardless of whether the original interaction
    has already been responded to. This avoids common API exceptions when
    sending followup messages.
    """
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(**kwargs)
        else:
            await interaction.followup.send(**kwargs)
    except discord.errors.NotFound:
        await interaction.followup.send(**kwargs)

# -------------------------------
# FILE PATHS & INITIAL SETUP
# -------------------------------
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")
token_file_path = os.path.join(os.path.dirname(__file__), "..", "INFO.txt")
error_log_file_path = os.path.join(DATA_FOLDER, "error_log.txt")
submitted_users_file_path = os.path.join(DATA_FOLDER, "submitted_users.txt")
role_data_file_path = os.path.join(DATA_FOLDER, "role_data.json")
titles_file_path = os.path.join(DATA_FOLDER, "Roles.txt")
challenges_file_path = os.path.join(DATA_FOLDER, "challenges.json")
user_data_file = os.path.join(DATA_FOLDER, "users.json")
riddles_file_path = os.path.join(DATA_FOLDER, "riddles.json")
riddle_scores_file_path = os.path.join(DATA_FOLDER, "riddle_scores.json")
shame_file_path = os.path.join(DATA_FOLDER, "shame.txt")

# -------------------------------
# Global Variables
# -------------------------------
toxined_users = set()
last_neurotoxin_date = {}
lfg_queue = {}

# -------------------------------
# Utility Functions, Load Functions, and Preloaded Data
# (These remain unchanged from your existing file)
# -------------------------------


def log_experiment(user_id):
    """Log completed experiment for a user and return total count."""
    user_data = load_users()
    if str(user_id) not in user_data["users"]:
        user_data["users"][str(user_id)] = {"experiments_completed": 0, "achievements": []}
    user_data["users"][str(user_id)]["experiments_completed"] += 1
    save_json(user_data_file, user_data)
    return user_data["users"][str(user_id)]["experiments_completed"]


def check_achievements(user_id):
    """Check and grant achievements based on experiment completion."""
    user_data = load_users()
    user_str = str(user_id)
    if user_str not in user_data["users"]:
        return []
    new_achievements = []
    experiments_completed = user_data["users"][user_str]["experiments_completed"]
    current_achievements = user_data["users"][user_str].get("achievements", [])
    if experiments_completed >= 5 and "Science Enthusiast" not in current_achievements:
        new_achievements.append("Science Enthusiast")
    if experiments_completed >= 10 and "Mad Scientist" not in current_achievements:
        new_achievements.append("Mad Scientist")
    if experiments_completed >= 20 and "Survivor of Science" not in current_achievements:
        new_achievements.append("Survivor of Science")
    if new_achievements:
        user_data["users"][user_str].setdefault("achievements", []).extend(new_achievements)
        save_json(user_data_file, user_data)
    return new_achievements


def update_riddle_score(user_id, correct):
    """Update riddle scores for a user."""
    user_str = str(user_id)
    if user_str not in riddle_scores["users"]:
        riddle_scores["users"][user_str] = {"correct_count": 0, "wrong_count": 0, "used_riddles": []}
    if correct:
        riddle_scores["users"][user_str]["correct_count"] += 1
    else:
        riddle_scores["users"][user_str]["wrong_count"] += 1
    save_json(riddle_scores_file_path, riddle_scores)
    return riddle_scores["users"][user_str]["correct_count"]


def load_riddles():
    """Load riddles from riddles.json."""
    if not os.path.isfile(riddles_file_path):
        print(f"ERROR: {riddles_file_path} not found.")
        return []
    try:
        with open(riddles_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: {riddles_file_path} has invalid JSON format.")
        return []


def load_shame_lines():
    """Load lines of sarcasm from shame.txt."""
    if not os.path.isfile(shame_file_path):
        return ["Shame file not found! No insults available."]
    with open(shame_file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
        return lines if lines else ["No insults in the shame file!"]


def load_riddle_scores():
    """Load or create riddle_scores.json."""
    if not os.path.isfile(riddle_scores_file_path):
        with open(riddle_scores_file_path, "w", encoding="utf-8") as f:
            json.dump({"users": {}}, f)
    try:
        with open(riddle_scores_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for user in data["users"].values():
                if "used_riddles" not in user:
                    user["used_riddles"] = []
            return data
    except json.JSONDecodeError:
        return {"users": {}}


def load_users():
    """Load user data from users.json."""
    if not os.path.isfile(user_data_file):
        return {"users": {}}
    try:
        with open(user_data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"users": {}}


def load_challenges():
    """Load challenges from challenges.json."""
    if not os.path.isfile(challenges_file_path):
        print(f"ERROR: {challenges_file_path} not found.")
        return []
    try:
        with open(challenges_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: {challenges_file_path} has invalid JSON format.")
        return []


# Preload data
riddles_data = load_riddles()
shame_lines = load_shame_lines()
riddle_scores = load_riddle_scores()

# -------------------------------
# Command Cog Class
# -------------------------------
class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='info', description="Display server information.")
    async def info(self, interaction: discord.Interaction):
        server = interaction.guild
        embed = discord.Embed(title=f"{server.name} Information", color=0xff0000)
        embed.add_field(name="Members", value=server.member_count)
        embed.add_field(name="Owner", value=server.owner.display_name)
        await safe_send(interaction, embed=embed)

    @app_commands.command(name='cakeorlie', description="Offer someone a choice between cake or truth.")
    async def cakeorlie(self, interaction: discord.Interaction, user: discord.Member):
        """Present a polite choice of cake or truth to a user."""
        response = f"{user.mention}, it's decision time: Cake 🍰 or Truth ☕?"
        await safe_send(interaction, content=response)

    @app_commands.command(name='companioncube', description="Entrust a virtual Companion Cube to someone.")
    async def companioncube(self, interaction: discord.Interaction, user: discord.Member):
        """Politely assign a Companion Cube to a user and ask them to care for it."""
        response = (f"{user.mention}, you have been graciously entrusted with a virtual Companion Cube. "
                   "Please see that it is well cared for. 🤖❤️")
        await safe_send(interaction, content=response)

    @app_commands.command(name='toxin', description="Deliver a gentle reprimand to a user.")
    async def toxin(self, interaction: discord.Interaction, user: discord.User):
        """Softened version of the neurotoxin command; politely admonish a user."""
        toxined_users.add(user.id)
        last_neurotoxin_date[user.id] = datetime.date.today()
        await safe_send(interaction, content=f"{user.name} has been gently reprimanded. Please take care in the future.")

    @app_commands.command(name='role', description="Assign a random role from available titles.")
    @app_commands.checks.cooldown(1, 600)
    async def role(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        guild = interaction.guild
        member = user if user is not None else interaction.user
        if os.path.exists(role_data_file_path):
            with open(role_data_file_path, 'r', encoding='utf-8') as file:
                try:
                    role_data = json.load(file)
                except json.JSONDecodeError:
                    role_data = {"used_titles": [], "assigned_roles": {}}
        else:
            role_data = {"used_titles": [], "assigned_roles": {}}
        if str(member.id) in role_data['assigned_roles']:
            assigned_at = datetime.datetime.fromisoformat(role_data['assigned_roles'][str(member.id)]['assigned_at'])
            cooldown_period = datetime.timedelta(days=7)
            if (datetime.datetime.now() - assigned_at) < cooldown_period:
                await safe_send(interaction, content=f'{member.mention} is still on cooldown for role assignment. Please wait before requesting again.')
                return
        if not os.path.isfile(titles_file_path):
            await safe_send(interaction, content="Roles.txt file not found.")
            return
        with open(titles_file_path, 'r', encoding='utf-8') as titles_file:
            titles = [line.strip() for line in titles_file.readlines() if line.strip()]
        available_titles = [title for title in titles if title not in role_data.get('used_titles', [])]
        if not available_titles:
            await safe_send(interaction, content='No available titles at the moment. Please try again later.')
            return
        title = random.choice(available_titles)
        role_color = discord.Color.random()
        try:
            role = await guild.create_role(name=title, permissions=discord.Permissions(268435456), color=role_color)
            await member.add_roles(role)
            role_data.setdefault('assigned_roles', {})[str(member.id)] = {
                'username': member.name,
                'role_name': title,
                'assigned_at': datetime.datetime.now().isoformat()
            }
            role_data.setdefault('used_titles', []).append(title)
            save_json(role_data_file_path, role_data)
            await safe_send(interaction, content=f'Role "{title}" assigned successfully to {member.mention}')
        except discord.Forbidden:
            await safe_send(interaction, content="I don't have permission to manage roles.")
        except Exception as e:
            await safe_send(interaction, content=f'Failed to assign role. Error: {str(e)}')

    @app_commands.command(name='experiment', description="Start a random experiment challenge.")
    async def experiment(self, interaction: discord.Interaction):
        challenges = load_challenges()
        if not challenges:
            await safe_send(interaction, content="No challenges are defined!")
            return
        challenge = random.choice(challenges)
        user_id = interaction.user.id
        await safe_send(interaction, content=f"{interaction.user.mention}, **{challenge['prompt']}**")
        challenge_msg = await interaction.original_response()
        if challenge["type"] == "react":
            emoji = challenge.get("emoji", "✅")
            await challenge_msg.add_reaction(emoji)

            def check_reaction(reaction, user):
                return (user.id == user_id and str(reaction.emoji) == emoji and reaction.message.id == challenge_msg.id)

            try:
                await self.bot.wait_for("reaction_add", timeout=challenge["timeout"], check=check_reaction)
                await self.complete_experiment(interaction, challenge["prompt"])
            except asyncio.TimeoutError:
                await interaction.followup.send(f"❌ **Failure**, {interaction.user.mention}. You didn't react in time.")
        elif challenge["type"] == "message":

            def check_message(m):
                if m.author.id != user_id:
                    return False
                if challenge.get("min_words", 0) > 0 and len(m.content.split()) < challenge["min_words"]:
                    return False
                if challenge.get("min_chars", 0) > 0 and len(m.content) < challenge["min_chars"]:
                    return False
                return True

            try:
                await self.bot.wait_for("message", timeout=challenge["timeout"], check=check_message)
                await self.complete_experiment(interaction, challenge["prompt"])
            except asyncio.TimeoutError:
                await interaction.followup.send(f"❌ **Failure**, {interaction.user.mention}. You didn't meet the message requirement in time.")

    async def complete_experiment(self, interaction: discord.Interaction, prompt: str):
        completed_count = log_experiment(interaction.user.id)
        new_achievements = check_achievements(interaction.user.id)
        response = (f"**Success!** {interaction.user.mention}, you completed the experiment:\n"
                    f"'{prompt}'\n"
                    f"Total Experiments: **{completed_count}**")
        if new_achievements:
            response += f"\n🎉 Achievement Unlocked: {', '.join(new_achievements)}!"
            if "Survivor of Science" in new_achievements:
                await self.assign_experiment_role(interaction, "Survivor of Science")
                response += f"\nRole **Survivor of Science** assigned!"
        await interaction.followup.send(response)

    @app_commands.command(name='riddle', description="Start a riddle challenge.")
    async def riddle(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        if not riddles_data:
            await safe_send(interaction, content="No riddles available!")
            return
        target_user = user if user else interaction.user
        if target_user.bot:
            await safe_send(interaction, content="You can't challenge a bot to a riddle.")
            return
        if target_user == interaction.user:
            await self.send_riddle(interaction, target_user)
        else:
            await safe_send(interaction, content=f"{target_user.mention}, do you accept the challenge? React with ✅ within 10 minutes!")
            challenge_msg = await interaction.original_response()
            await challenge_msg.add_reaction("✅")

            def check_reaction(reaction, reactor):
                return reactor == target_user and str(reaction.emoji) == "✅" and reaction.message.id == challenge_msg.id

            try:
                await self.bot.wait_for("reaction_add", timeout=600.0, check=check_reaction)
                await self.send_riddle(interaction, target_user)
            except asyncio.TimeoutError:
                await interaction.followup.send(f"⏳ {target_user.mention} took too long! No riddle for you.")

    async def send_riddle(self, interaction: discord.Interaction, user: discord.Member):
        riddle_obj = random.choice(riddles_data)
        riddle_text = riddle_obj.get("riddle", "No riddle text available.")
        riddle_answer = riddle_obj.get("answer", "").lower().strip()
        await safe_send(interaction, content=f"🔎 {user.mention}, here is your riddle:\n**{riddle_text}**\n*(You have 3 Minutes to answer!)*")

        def check_message(m):
            return m.author == user and m.channel == interaction.channel

        try:
            guess_msg = await self.bot.wait_for("message", timeout=180.0, check=check_message)
            user_guess = guess_msg.content.lower().strip()
            confirm_msg = await interaction.followup.send(f"🤔 {user.mention}, **is that your final answer?** React with ✅ to confirm.")
            await confirm_msg.add_reaction("✅")

            def check_confirmation(reaction, reactor):
                return (reactor == user and str(reaction.emoji) == "✅" and reaction.message.id == confirm_msg.id)

            try:
                await self.bot.wait_for("reaction_add", timeout=180.0, check=check_confirmation)
                if riddle_answer in user_guess:
                    correct_count = update_riddle_score(user.id, True)
                    await interaction.followup.send(f"✅ **Correct!** Well done, {user.mention}!")
                    await self.assign_riddle_roles(user, interaction.guild, correct_count)
                else:
                    update_riddle_score(user.id, False)
                    shame = random.choice(shame_lines)
                    await interaction.followup.send(f"❌ **Wrong!** {shame}")
            except asyncio.TimeoutError:
                await interaction.followup.send(f"⏳ {user.mention}, you took too long to confirm. Answer **not accepted**.")
        except asyncio.TimeoutError:
            update_riddle_score(user.id, False)
            await interaction.followup.send(f"⏳ {user.mention} took too long! No answer recorded.")

    @app_commands.command(name='riddlescore', description="Show global riddle scores for a user.")
    async def riddlescore(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        target_user = user if user else interaction.user
        user_str = str(target_user.id)
        if user_str not in riddle_scores["users"]:
            await safe_send(interaction, content=f"{target_user.mention} hasn't answered any riddles yet.")
            return
        stats = riddle_scores["users"][user_str]
        c = stats.get("correct_count", 0)
        w = stats.get("wrong_count", 0)
        await safe_send(interaction, content=f"🏆 **Global Riddle Score for {target_user.mention}**:\n✅ Correct: {c}\n❌ Wrong: {w}")

    @app_commands.command(name='science', description="Fetch the latest science news with a butler's flourish.")
    async def science(self, interaction: discord.Interaction):
        """Retrieve and present a random science article in a courteous tone."""
        try:
            page = random.randint(1, 3)
            url = f"{SCIENCE_NEWS_BASE_URL}&pageSize=20&page={page}&apiKey={NEWS_API_KEY}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles")
            if not articles:
                await safe_send(interaction, content="No groundbreaking science news at the moment. My apologies.")
                return
            article = random.choice(articles)
            title = article.get("title", "No title")
            article_url = article.get("url", "No URL provided")
            # Butler‑style comments replacing GLaDOS snark
            butler_comments = [
                "May I present a fascinating discovery for your consideration.",
                "If I may, this piece of science news might pique your interest.",
                "Here is a noteworthy advancement you might find enlightening.",
                "Permit me to draw your attention to this recent scientific accomplishment.",
                "I humbly offer this scientific tidbit for your perusal."
            ]
            comment = random.choice(butler_comments)
            msg = (
                f"{interaction.user.mention}, I have found something of interest for you:\n\n"
                f"**{title}**\n{article_url}\n\n{comment}"
            )
            await safe_send(interaction, content=msg)
        except Exception as e:
            await safe_send(interaction, content=f"Error retrieving news: {e}")

    @app_commands.command(name='steamlookup', description="Look up a game on Steam.")
    async def steamlookup(self, interaction: discord.Interaction, *, game_name: str):
        url = f"https://store.steampowered.com/api/storesearch/?cc=US&l=en&term={game_name}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("items"):
                game = data["items"][0]
                title = game["name"]
                appid = game["id"]
                store_url = f"https://store.steampowered.com/app/{appid}"
                await safe_send(interaction, content=f"🎮 **{title}** - [Steam Store Link]({store_url})")
            else:
                await safe_send(interaction, content="❌ No game found on Steam.")
        else:
            await safe_send(interaction, content="⚠️ Error fetching data from Steam.")

    @app_commands.command(name='leaderboard', description="Display a global leaderboard for experiments and riddle scores.")
    async def leaderboard(self, interaction: discord.Interaction):
        user_data = load_users()
        experiments_list = []
        for user_id, data in user_data.get("users", {}).items():
            try:
                uid = int(user_id)
            except ValueError:
                continue
            experiments = data.get("experiments_completed", 0)
            experiments_list.append((uid, experiments))
        experiments_list.sort(key=lambda x: x[1], reverse=True)

        experiments_text = ""
        for idx, (uid, experiments) in enumerate(experiments_list[:10], start=1):
            user_obj = interaction.client.get_user(uid)
            if user_obj is None:
                try:
                    user_obj = await interaction.client.fetch_user(uid)
                except Exception:
                    user_name = f"User {uid}"
                else:
                    user_name = user_obj.name
            else:
                user_name = user_obj.name
            experiments_text += f"{idx}. {user_name} - {experiments} experiments\n"

        riddle_list = []
        for user_id, data in riddle_scores.get("users", {}).items():
            try:
                uid = int(user_id)
            except ValueError:
                continue
            correct = data.get("correct_count", 0)
            wrong = data.get("wrong_count", 0)
            riddle_list.append((uid, correct, wrong))
        riddle_list.sort(key=lambda x: x[1], reverse=True)

        riddle_text = ""
        for idx, (uid, correct, wrong) in enumerate(riddle_list[:10], start=1):
            user_obj = interaction.client.get_user(uid)
            if user_obj is None:
                try:
                    user_obj = await interaction.client.fetch_user(uid)
                except Exception:
                    user_name = f"User {uid}"
                else:
                    user_name = user_obj.name
            else:
                user_name = user_obj.name
            riddle_text += f"{idx}. {user_name} - Correct: {correct}, Wrong: {wrong}\n"

        embed = discord.Embed(title="Global Leaderboard", color=discord.Color.blue())
        embed.add_field(
            name="Experiments Leaderboard",
            value=experiments_text if experiments_text else "No data available.",
            inline=False
        )
        embed.add_field(
            name="Riddle Score Leaderboard",
            value=riddle_text if riddle_text else "No data available.",
            inline=False
        )
        await safe_send(interaction, embed=embed)

    async def assign_experiment_role(self, interaction, role_name):
        try:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if not role:
                role = await interaction.guild.create_role(
                    name=role_name,
                    color=discord.Color.gold(),
                    reason="Achievement unlocked"
                )
            await interaction.user.add_roles(role)
            return True
        except Exception as e:
            print(f"Error assigning role: {e}")
            return False

    async def assign_riddle_roles(self, user, guild, correct_count):
        try:
            role_thresholds = {5: "Riddle Solver", 10: "Riddle Master", 20: "Enigma Champion"}
            for threshold, role_name in role_thresholds.items():
                if correct_count >= threshold:
                    role = discord.utils.get(guild.roles, name=role_name)
                    if not role:
                        role = await guild.create_role(
                            name=role_name,
                            color=discord.Color.blue(),
                            reason="Riddle achievement unlocked"
                        )
                    if role not in user.roles:
                        await user.add_roles(role)
                        for channel in guild.text_channels:
                            try:
                                await channel.send(f"🎉 {user.mention} has earned the **{role_name}** role!")
                                break
                            except discord.Forbidden:
                                continue
        except Exception as e:
            print(f"Error assigning riddle role: {e}")

    # -------------------------------
    # NEW MUSIC COMMANDS (via separate cog, but listed here for the command list)
    # -------------------------------
    # The actual implementations for /urlmusic, /randommusic, /skip, and /stop are in the Music cog.
    # Here, we just include them in the flashy command list for reference.
    @app_commands.command(name='commands', description="Display a flashy list of all available commands.")
    async def commands_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="✨ Command Arsenal",
            description="Feast your eyes on my dazzling repertoire of commands:",
            color=discord.Color.purple()
        )
        embed.add_field(name="/info", value="Display server information.", inline=True)
        embed.add_field(name="/cakeorlie", value="Offer someone a choice: Cake 🍰 or Truth ☕?", inline=True)
        embed.add_field(name="/companioncube", value="Entrust a virtual Companion Cube.", inline=True)
        embed.add_field(name="/toxin", value="Deliver a gentle reprimand to a user.", inline=True)
        embed.add_field(name="/role", value="Assign a random role from quirky titles.", inline=True)
        embed.add_field(name="/experiment", value="Initiate a random experiment challenge.", inline=True)
        embed.add_field(name="/riddle", value="Challenge someone with a riddle.", inline=True)
        embed.add_field(name="/riddlescore", value="Show global riddle scores.", inline=True)
        embed.add_field(name="/science", value="Fetch the latest science news with a butler's flourish.", inline=True)
        embed.add_field(name="/steamlookup", value="Look up a game on Steam.", inline=True)
        embed.add_field(name="/leaderboard", value="Display the global leaderboard for experiments and riddles.", inline=True)
        embed.add_field(name="/urlmusic", value="Stream music from a URL.", inline=True)
        embed.add_field(name="/randommusic", value="Play a random local music file.", inline=True)
        embed.add_field(name="/skip", value="Skip the current track.", inline=True)
        embed.add_field(name="/stop", value="Stop playback and disconnect.", inline=True)
        embed.add_field(name="/commands", value="Display this command list.", inline=True)
        embed.set_footer(text="That's the full extent of my dazzling capabilities!")
        await safe_send(interaction, embed=embed)


async def setup(bot: commands.Bot):
    try:
        await bot.add_cog(Commands(bot))
        print("Successfully added commands cog")
    except Exception as e:
        print(f"Error during setup: {e}")
