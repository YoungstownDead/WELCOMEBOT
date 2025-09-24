import discord
from discord import app_commands, Interaction
from discord.ext import commands
import os
import random
import asyncio

MUSIC_FOLDER = r"C:\Users\young\Music"  # <-- Update this to your actual music folder

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_clients = {}
        self.audio_queue = {}

    def parse_file_name(self, file_path: str) -> (str, str):
        """Attempt to parse 'Song Title - Artist' from a filename."""
        base = os.path.basename(file_path)
        name_no_ext, _ = os.path.splitext(base)
        parts = [p.strip() for p in name_no_ext.split('-')]

        if len(parts) >= 2:
            artist = parts[-1]
            title = '-'.join(parts[:-1]).strip()
            return (title, artist)
        else:
            return (name_no_ext, "")

    async def rename_voice_channel(self, guild: discord.Guild, song_name: str = None):
        """Renames the voice channel to reflect what's currently playing."""
        try:
            voice_client = self.voice_clients.get(guild.id)
            if voice_client and voice_client.channel:
                channel = voice_client.channel
                if song_name:
                    new_name = f"Music 🎵 {song_name}"[:100]  # Truncate for safety
                else:
                    new_name = "Music 🎵 Idle..."

                print(f"[DEBUG] Attempting to rename channel {channel.name} -> {new_name}")
                await channel.edit(name=new_name)
        except Exception as e:
            print(f"[ERROR] Failed to rename channel: {e}")

    async def play_next(self, guild_id: int):
        """Plays the next song in the queue, updates channel name, and loops."""
        if guild_id in self.audio_queue and self.audio_queue[guild_id]:
            next_song = self.audio_queue[guild_id].pop(0)
            voice_client = self.voice_clients.get(guild_id)
            if voice_client and voice_client.is_connected():
                # Add a small delay to avoid spamming rename & playback
                await asyncio.sleep(1)

                # Play the next track
                source = discord.FFmpegPCMAudio(next_song)
                voice_client.play(
                    source,
                    after=lambda e: self.bot.loop.create_task(self.play_next(guild_id))
                )
                # Parse the song name
                song_title, artist = self.parse_file_name(next_song)
                display_name = song_title
                if artist:
                    display_name += f" - {artist}"

                # Rename the channel
                await self.rename_voice_channel(voice_client.guild, display_name)

                print(f"[DEBUG] Now playing: {next_song}")
            else:
                self.voice_clients.pop(guild_id, None)
        else:
            print(f"[DEBUG] Queue for guild {guild_id} is empty or missing.")

    @app_commands.command(name="randommusic", description="Play a random music file continuously.")
    async def randommusic(self, interaction: Interaction):
        """Shuffle & play local music in the voice channel."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "You must be in a voice channel to use this command!",
                ephemeral=True
            )
            return

        voice_channel = interaction.user.voice.channel
        if not os.path.isdir(MUSIC_FOLDER):
            await interaction.response.send_message("Music folder not found.", ephemeral=True)
            return

        # Gather files
        accepted_extensions = ('.mp3', '.wav', '.opus', '.flac', '.m4a')
        audio_files = [
            os.path.join(root, file)
            for root, _, files in os.walk(MUSIC_FOLDER)
            for file in files
            if file.lower().endswith(accepted_extensions)
        ]

        if not audio_files:
            await interaction.response.send_message("No audio files found.", ephemeral=True)
            return

        if interaction.guild_id not in self.audio_queue:
            self.audio_queue[interaction.guild_id] = random.sample(audio_files, len(audio_files))

        # Connect the bot if needed
        if (
            interaction.guild_id not in self.voice_clients
            or not self.voice_clients[interaction.guild_id].is_connected()
        ):
            self.voice_clients[interaction.guild_id] = await voice_channel.connect()
            print("[DEBUG] Connected to voice channel.")

        first_song = self.audio_queue[interaction.guild_id][0]
        song_title, artist = self.parse_file_name(first_song)
        display_name = song_title
        if artist:
            display_name += f" - {artist}"

        await interaction.response.send_message(
            f"Now playing: {display_name}",
            ephemeral=True
        )
        self.bot.loop.create_task(self.play_next(interaction.guild_id))

    @app_commands.command(name="skip", description="Skip the current song.")
    async def skip(self, interaction: Interaction):
        """Stop current track, going straight to the next."""
        voice_client = self.voice_clients.get(interaction.guild_id)
        if voice_client and voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("Skipped the song!", ephemeral=True)
            print("[DEBUG] Song skipped.")
        else:
            await interaction.response.send_message("No song is playing.", ephemeral=True)
            print("[DEBUG] Skip requested but no song playing.")

    @app_commands.command(name="stop", description="Stop playback and disconnect the bot.")
    async def stop(self, interaction: Interaction):
        """Stop playback, disconnect, reset channel name."""
        voice_client = self.voice_clients.get(interaction.guild_id)
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            self.voice_clients.pop(interaction.guild_id, None)
            self.audio_queue.pop(interaction.guild_id, None)

            # Reset channel name
            await self.rename_voice_channel(interaction.guild, None)

            await interaction.response.send_message(
                "Playback stopped and bot disconnected.",
                ephemeral=True
            )
            print("[DEBUG] Bot disconnected and channel renamed to Idle...")
        else:
            await interaction.response.send_message(
                "Bot is not connected to a voice channel.",
                ephemeral=True
            )
            print("[DEBUG] Stop requested but not connected.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
