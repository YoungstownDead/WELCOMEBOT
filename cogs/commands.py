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
# Helper for safe messaging
# -------------------------------
async def safe_send(interaction: discord.Interaction, **kwargs):
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(**kwargs)
        else:
            await interaction.followup.send(**kwargs)
    except discord.errors.NotFound:
        await interaction.followup.send(**kwargs)

# -------------------------------
# Command Cog Class (no music)
# -------------------------------
class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='info', description="Display server information.")
    async def info(self, interaction: discord.Interaction):
        server = interaction.guild
        embed = discord.Embed(title=f"{server.name} Information", color=0x008080)
        embed.add_field(name="Members", value=server.member_count)
        embed.add_field(name="Owner", value=server.owner.display_name)
        await safe_send(interaction, embed=embed)

    @app_commands.command(name='cakeorlie', description="A polite choice: Cake 🍰 or Truth ☕.")
    async def cakeorlie(self, interaction: discord.Interaction, user: discord.Member):
        response = f"{user.mention}, pray tell — will you choose Cake 🍰 or Truth ☕?"
        await safe_send(interaction, content=response)

    @app_commands.command(name='companioncube', description="Assign a virtual Companion Cube.")
    async def companioncube(self, interaction: discord.Interaction, user: discord.Member):
        response = f"{user.mention}, you’ve been entrusted with a Companion Cube. Treat it with care. 🎁"
        await safe_send(interaction, content=response)

    @app_commands.command(name='toxin', description="Deliver a gentle reprimand.")
    async def toxin(self, interaction: discord.Interaction, user: discord.User):
        await safe_send(interaction, content=f"{user.name} has been ever so gently reprimanded.")

    @app_commands.command(name='science', description="Fetch the latest science news.")
    async def science(self, interaction: discord.Interaction):
        polite_comments = [
            "If I may, here is a fascinating discovery.",
            "Might I present this scientific update for your interest.",
            "Allow me to share this advancement, most enlightening indeed."
        ]
        try:
            url = f"https://newsapi.org/v2/top-headlines?category=science&language=en&apiKey=YOUR_API_KEY"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            articles = data.get("articles")
            if not articles:
                await safe_send(interaction, content="No science news at this time, sir.")
                return
            article = random.choice(articles)
            title = article.get("title", "No title")
            article_url = article.get("url", "No URL")
            comment = random.choice(polite_comments)
            msg = f"{interaction.user.mention}, {comment}\n\n**{title}**\n{article_url}"
            await safe_send(interaction, content=msg)
        except Exception as e:
            await safe_send(interaction, content=f"Error retrieving news: {e}")

    @app_commands.command(name='commands', description="Display available commands.")
    async def commands_list(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📜 Command List",
            description="Here are my current services, at your disposal:",
            color=discord.Color.blue()
        )
        embed.add_field(name="/info", value="Display server information.", inline=True)
        embed.add_field(name="/cakeorlie", value="A polite choice: Cake 🍰 or Truth ☕.", inline=True)
        embed.add_field(name="/companioncube", value="Assign a virtual Companion Cube.", inline=True)
        embed.add_field(name="/toxin", value="Deliver a gentle reprimand.", inline=True)
        embed.add_field(name="/science", value="Fetch the latest science news.", inline=True)
        embed.add_field(name="/commands", value="Display this command list.", inline=True)
        embed.set_footer(text="At your service.")
        await safe_send(interaction, embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Commands(bot))
