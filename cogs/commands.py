import os
import random
import json
import asyncio
import datetime
from typing import Any, Optional

import discord
from discord import app_commands
from discord.ext import commands
import requests  # For API calls

from utils.gpt_client import (
    GPT_API_KEY,
    DEFAULT_SYSTEM_PROMPT,
    gpt_is_configured,
    get_openai_client,
    request_chat_completion,
)

# -------------------------------
# Setup
# -------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

openai_client: Optional[Any] = get_openai_client()

# -------------------------------
# Safe send helper
# -------------------------------
async def safe_send(interaction: discord.Interaction, **kwargs):
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(**kwargs)
        else:
            await interaction.followup.send(**kwargs)
    except Exception as e:
        # fallback log or error send
        if not interaction.response.is_done():
            await interaction.response.send_message(content=f"Error: {e}")
        else:
            await interaction.followup.send(content=f"Error: {e}")

# -------------------------------
# Commands
# -------------------------------
class MyBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="info", description="Display server information.")
    async def info(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"Info for {guild.name}",
            description="Here are some server details:",
            color=discord.Color.green()
        )
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.set_footer(text="At your service.")
        await safe_send(interaction, embed=embed)

    @app_commands.command(name="cakeorlie", description="Cake 🍰 or Truth ☕?")
    async def cakeorlie(self, interaction: discord.Interaction):
        choice = random.choice(["Cake 🍰", "Truth ☕"])
        await safe_send(interaction, content=f"{interaction.user.mention}, you chose: **{choice}**")

    @app_commands.command(name="companioncube", description="Assign a virtual Companion Cube.")
    async def companioncube(self, interaction: discord.Interaction, user: discord.Member):
        await safe_send(interaction, content=f"{user.mention}, you’ve been gifted a weighted Companion Cube 🎁")

    @app_commands.command(name="toxin", description="Deliver a gentle reprimand.")
    async def toxin(self, interaction: discord.Interaction, user: discord.User):
        await safe_send(interaction, content=f"{user.name} has been ever so gently reprimanded.")

    @app_commands.command(name="science", description="Fetch the latest science news.")
    async def science(self, interaction: discord.Interaction):
        polite_comments = [
            "If I may, here is a fascinating discovery.",
            "Might I present this scientific update for your interest.",
            "Allow me to share this advancement, most enlightening indeed."
        ]
        try:
            url = f"https://newsapi.org/v2/top-headlines?category=science&language=en&apiKey=YOUR_API_KEY"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles")
            if not articles:
                await safe_send(interaction, content="No science news at this time.")
                return
            article = random.choice(articles)
            title = article.get("title", "No title")
            article_url = article.get("url", "No URL")
            comment = random.choice(polite_comments)
            msg = f"{interaction.user.mention}, {comment}\n\n**{title}**\n{article_url}"
            await safe_send(interaction, content=msg)
        except Exception as e:
            await safe_send(interaction, content=f"Error retrieving news: {e}")

    @app_commands.command(name="commands", description="Display available commands.")
    async def commands_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📜 Command List",
            description="Here are my current services:",
            color=discord.Color.blue()
        )
        embed.add_field(name="/info", value="Display server information.", inline=True)
        embed.add_field(name="/cakeorlie", value="Cake 🍰 or Truth ☕.", inline=True)
        embed.add_field(name="/companioncube", value="Assign a virtual Companion Cube.", inline=True)
        embed.add_field(name="/toxin", value="Deliver a gentle reprimand.", inline=True)
        embed.add_field(name="/science", value="Fetch the latest science news.", inline=True)
        embed.add_field(name="/askgpt", value="Consult GPT for a thoughtful reply.", inline=True)
        embed.add_field(name="/commands", value="Display this command list.", inline=True)
        embed.set_footer(text="At your service.")
        await safe_send(interaction, embed=embed)

    @app_commands.command(name="askgpt", description="Consult GPT for a thoughtful reply.")
    @app_commands.describe(prompt="The query you would like me to relay to GPT.")
    async def askgpt(self, interaction: discord.Interaction, prompt: str):
        if not GPT_API_KEY or not gpt_is_configured() or not openai_client:
            await safe_send(interaction, content="I regret to inform you that no GPT API key was configured.")
            return

        # Defer to avoid interaction timeout
        await interaction.response.defer(thinking=True)

        try:
            message = await request_chat_completion(
                prompt,
                system_prompt=DEFAULT_SYSTEM_PROMPT,
            )
            if not message:
                message = "GPT returned no content, I'm afraid."

            await interaction.followup.send(
                f"{interaction.user.mention}, GPT suggests:\n\n{message}"
            )
        except Exception as e:
            await interaction.followup.send(f"Error: {e}")


# -------------------------------
# Cog / Bot Setup
# -------------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(MyBot(bot))

# Run like normal with bot.run("YOUR_TOKEN")
