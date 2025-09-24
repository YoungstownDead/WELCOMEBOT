import discord
from discord import app_commands, Interaction
from discord.ext import commands
import os
import json

# We'll reuse your existing user data file structure so achievements are consistent
DATA_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data")
USER_DATA_FILE = os.path.join(DATA_FOLDER, "users.json")

def load_user_data():
    """Load user data from users.json (or create if missing)."""
    if not os.path.isfile(USER_DATA_FILE):
        return {"users": {}}
    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"users": {}}

def save_user_data(data: dict):
    """Save user data back to users.json."""
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

class BugReportModal(discord.ui.Modal, title="Bug Report"):
    """A modal collecting info about a bug, awarding achievements upon submission."""
    description = discord.ui.TextInput(
        label="Description of the Bug",
        style=discord.TextStyle.paragraph,
        required=True,
        placeholder="Describe the bug in detail..."
    )
    repro_steps = discord.ui.TextInput(
        label="Steps to Reproduce (Optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        placeholder="List the steps to reproduce the bug..."
    )
    screenshot_url = discord.ui.TextInput(
        label="Screenshot URL (Optional)",
        style=discord.TextStyle.short,
        required=False,
        placeholder="Paste an image link if any..."
    )

    def __init__(self, parent_cog):
        super().__init__()
        self.parent_cog = parent_cog

    async def on_submit(self, interaction: discord.Interaction):
        """Triggered when the user presses 'Submit' on the modal."""
        user_id_str = str(interaction.user.id)
        user_data = load_user_data()

        # If user doesn't exist in the data, create their entry
        if user_id_str not in user_data["users"]:
            user_data["users"][user_id_str] = {
                "experiments_completed": 0,
                "achievements": []
            }

        achievements = user_data["users"][user_id_str].get("achievements", [])

        # Condition 1: Provided a detailed description (100+ chars)
        if len(self.description.value) >= 100:
            if "Thorough Reporter" not in achievements:
                achievements.append("Thorough Reporter")

        # Condition 2: Provided repro steps
        if self.repro_steps.value:
            if "Detailed Steps" not in achievements:
                achievements.append("Detailed Steps")

        # Condition 3: Provided a screenshot URL
        if self.screenshot_url.value:
            if "Visual Evidence" not in achievements:
                achievements.append("Visual Evidence")

        # Condition 4: If user got all 3 above in a single submission
        # (i.e. they wrote a 100+ char description, repro steps, AND screenshot)
        # => Award "Data Detective"
        if all(
            ach in achievements
            for ach in ("Thorough Reporter", "Detailed Steps", "Visual Evidence")
        ):
            if "Data Detective" not in achievements:
                achievements.append("Data Detective")

        # Save updated achievements
        user_data["users"][user_id_str]["achievements"] = achievements
        save_user_data(user_data)

        # Build a response message
        response_msg = (
            f"Thanks for your report, {interaction.user.mention}!\n"
            f"**Current Achievements:** {', '.join(achievements)}"
        )

        # Example: if they just unlocked "Data Detective," award a special role
        # or if they have "Detailed Steps" at least, they get "Community Supporter"
        # (just as an example)
        new_role_name = None
        if "Data Detective" in achievements:
            new_role_name = "Data Detective"
        elif "Detailed Steps" in achievements:
            new_role_name = "Community Supporter"

        # If a new role is decided, attempt to grant it
        if new_role_name is not None:
            try:
                # Try to find the role by name
                role = discord.utils.get(interaction.guild.roles, name=new_role_name)
                if not role:
                    # If not found, create it (bot needs 'Manage Roles')
                    role = await interaction.guild.create_role(
                        name=new_role_name,
                        color=discord.Color.blue(),
                        reason="Achievement unlocked"
                    )
                # Add role if user doesn't have it
                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role)
                    response_msg += f"\n**Achievement Role** `{new_role_name}` granted!"
            except discord.Forbidden:
                response_msg += "\n*(I don't have permission to create/manage roles!)*"
            except Exception as e:
                response_msg += f"\n*(Error assigning role: {e})*"

        # Finally respond
        await interaction.response.send_message(response_msg, ephemeral=True)

class GamifiedModalCog(commands.Cog):
    """Cog that holds a /bugreport command, awarding achievements for thoroughness."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="bugreport", description="Report a bug and earn achievements!")
    async def bugreport(self, interaction: discord.Interaction):
        """Opens a Bug Report modal. Earn achievements by filling out the fields thoroughly."""
        modal = BugReportModal(self)  # pass parent cog
        await interaction.response.send_modal(modal)

async def setup(bot: commands.Bot):
    """Called by bot.load_extension to set up the Cog."""
    await bot.add_cog(GamifiedModalCog(bot))
