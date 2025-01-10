import os
import json
import random

import asyncio
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
from discord import FFmpegPCMAudio


SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


class GuessTheSongGame:
    def __init__(self, bot, text_channel, voice_channel, players):
        self.bot = bot
        self.text_channel = text_channel
        self.voice_channel = voice_channel
        self.players = players
        self.current_song = None
        self.current_song_url = None
        self.current_playlist = None
        self.scores = {player: 0 for player in players}
        self.question_counter = 0
        self.question_active = False
        self.lock = asyncio.Lock()
        self.song_active = False
        self.spotify = None
        self.voice_client = None


    def _initialize_spotify(self):
        """Initialize the Spotify client."""
        client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
        self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


    def _get_game_playlist(self):
        """Get a playlist of songs for the game."""
        return self.spotify.user_playlist_tracks('spotify', '0R1oMVYDw6vfSaCrRjUvLJ')


    def _get_youtube_url_from_song(self, song, artists):
        query = f"{song} {' '.join(artists)} lyrics"
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            response = ydl.extract_info(f"ytsearch:{query}", download=False)
            return response['entries'][0]['original_url']


    async def join_voice_channel(self):
        try:
            self.voice_client = await self.voice_channel.connect()
            return True
        except Exception as e:
            print(e)
            await self.text_channel.send(f"Error joining voice channel")
            return False


    async def leave_voice_channel(self):
        await self.voice_client.disconnect()
        self.voice_client = None


    async def play_song(self):
        if not self.voice_client or not self.voice_client.is_connected():
            await self.text_channel.send("Error: Not connected to a voice channel.")
            return
        
        if not self.current_song_url:
            await self.text_channel.send("Error: No song URL found.")
            return
        
        ffmpeg_options = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
        }

        source = FFmpegPCMAudio(self.current_song_url, **ffmpeg_options)
        self.voice_client.play(source)

        await self.text_channel.send(f"Song now playing! Guess the song!")


    async def stop_song(self):
        if not self.voice_client or not self.voice_client.is_connected():
            await self.text_channel.send("Error: Not connected to a voice channel.")
            return
        
        self.voice_client.stop()


    async def start_game(self):
        # Initialize the Spotify client, if possible
        try:
            self._initialize_spotify()
        except Exception as e:
            await self.text_channel.send(f"Error initializing Spotify client, contact an administrator.")
            return
        
        # Get the game playlist
        self.current_playlist = self._get_game_playlist()

        # await asyncio.sleep(20)
        await self.ask_song()


    async def ask_song(self):
        # Check if there is a current playlist
        if not self.current_playlist:
            await self.text_channel.send("Error: No playlist found.")
            return

        # Check if there have been 5 questions asked
        if self.question_counter % 5 == 0:
            await self.text_channel.send('Current leaderboard:')
            await self.display_leaderboard()

        # Get a random song from the playlist
        # FIXME: Handle case when there are more than 100 songs in playlist, and need to get the next page
        tracks = self.current_playlist['items']

        songs_and_artists = {}
        for track in tracks:
            songs_and_artists[track['track']['name']] = [artist['name'] for artist in track['track']['artists']]
        
        song = random.choice(list(songs_and_artists.keys()))
        artists = songs_and_artists[song]
        self.current_song = song
        self.current_song_url = self._get_youtube_url_from_song(song, artists)
        
        if self.voice_client and self.voice_client.is_connected():
            await self.play_song()
        else:
            await self.text_channel.send("Error: Not connected to a voice channel.")
            return

        self.question_counter += 1


    async def display_leaderboard(self, final=False):
        """
        Display the leaderboard, either as a final summary or current standings.
        """
        leaderboard = sorted(self.scores.items(), key=lambda item: item[1], reverse=True)
        leaderboard_message = "\n".join([f"{player.mention}: {score}" for player, score in leaderboard])
        title = "Final Leaderboard:" if final else "Current Leaderboard:"
        await self.text_channel.send(f"{title}\n{leaderboard_message}")


    async def end_game(self):
        await self.text_channel.send("Game over!")
        await self.display_leaderboard(final=True)
