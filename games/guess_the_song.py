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
        self.current_artists = []
        self.current_song_url = None
        self.current_playlist = None
        self.scores = {player: 0 for player in players}
        self.question_counter = 0
        self.question_active = False
        self.lock = asyncio.Lock()
        self.spotify = None
        self.voice_client = None
        self.song_guessed = False
        self.guessed_artists_correct = []
        self.artists_guessed = False


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
            return response['entries'][0]['url']


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
        self.current_artists = artists

        if self.voice_client and self.voice_client.is_connected():
            await self.play_song()
        else:
            await self.text_channel.send("Error: Not connected to a voice channel.")
            return

        self.question_counter += 1
        self.question_active = True


    async def handle_answer(self, message):
        """
        Checks if a user's message matches the correct answer.
        """
        async with self.lock:
            if not self.current_song or not self.question_active:
                return
            
            correct_song = self.current_song.lower()
            correct_artists = [artist.lower() for artist in self.current_artists]

            # Check if the message content matches the correct song or artist until all answers are found
            user_guess = message.content.lower()
            user = message.author

            # Case when the user guesses the song
            if not self.song_guessed and user_guess == correct_song:
                self.song_guessed = True
                self.scores[user] += 1
                await self.text_channel.send(f"{user.mention} guessed the song, {correct_song}!")

            # Case when the user guesses an artist
            if not self.artists_guessed and user_guess in correct_artists:
                # Add the artist to the list of correct artists guessed
                self.guessed_artists_correct.append(user_guess)
                # Check if all artists have been guessed
                if len(self.guessed_artists_correct) == len(self.current_artists):
                    self.artists_guessed = True
                # Update the user's score for correct guess
                self.scores[user] += 1
                await self.text_channel.send(f"{user.mention} guessed an artist, {user_guess}!")
                # Remove the correct artist from the list of correct artists
                correct_artists.remove(user_guess)

            # Case when both the song and all artists have been guessed
            if self.song_guessed and self.artists_guessed:
                await self.text_channel.send(f"All artists and the song have been guessed! Correct song: {self.current_song} by {', '.join(self.guessed_artists_correct)}")
                await self.stop_song()
                self.question_active = False
                self.song_guessed = False
                self.artists_guessed = False
                self.guessed_artists_correct = []

                # Check if there have been 5 questions asked
                if self.question_counter % 5 == 0:
                    await self.display_leaderboard()
                    await asyncio.sleep(5)

                await asyncio.sleep(5)
                await self.text_channel.send("Next song starting now!")
                await self.ask_song()


    async def reveal_answer(self):
        """
        Reveals the current song because nobody guessed it/'idk' was ran
        """
        if not self.current_song or not self.question_active:
            await self.text_channel.send("Error: No question active.")
            return
        
        correct_artists = ', '.join(self.current_artists)
        await self.text_channel.send(f"The correct song was: {self.current_song} by {correct_artists}")
        await self.stop_song()

        self.question_active = False
        self.song_guessed = False
        self.artists_guessed = False
        self.guessed_artists_correct = []

        # Check if there have been 5 questions asked
        if self.question_counter % 5 == 0:
            await self.display_leaderboard()
            await asyncio.sleep(5)
        
        await asyncio.sleep(5)
        await self.text_channel.send("Next song starting now!")
        await self.ask_song()


    async def display_leaderboard(self, final=False):
        """
        Display the leaderboard, either as a final summary or current standings.
        """
        leaderboard = sorted(self.scores.items(), key=lambda item: item[1], reverse=True)
        leaderboard_message = "\n".join([f"{player.mention}: {score}" for player, score in leaderboard])
        title = "Final Leaderboard:" if final else "Current Leaderboard:"
        await self.text_channel.send(f"{title}\n{leaderboard_message}")


    async def end_game(self):
        # await self.text_channel.send("Game over!")
        await self.display_leaderboard(final=True)
        await self.stop_song()
        await self.leave_voice_channel()
