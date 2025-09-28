import json
import discord

async def safe_send(interaction: discord.Interaction, **kwargs):
    """
    Attempts to send a message using the initial interaction response if possible;
    if that fails, it sends a follow-up message instead.
    """
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(**kwargs)
        else:
            await interaction.followup.send(**kwargs)
    except discord.errors.NotFound:
        await interaction.followup.send(**kwargs)

def save_json(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_json(file_path):
    """Load JSON data from a file; returns an empty dict if not found or invalid."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Conversation history helpers
def get_user_history(user_id, file_path):
    data = load_json(file_path)
    return data.get(str(user_id), [])

def append_user_message(user_id, message, file_path):
    import datetime
    data = load_json(file_path)
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = []
    data[user_id].append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "message": message
    })
    save_json(file_path, data)

def clear_user_history(user_id, file_path):
    data = load_json(file_path)
    user_id = str(user_id)
    if user_id in data:
        data[user_id] = []
        save_json(file_path, data)
