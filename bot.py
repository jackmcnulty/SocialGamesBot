import os
from typing import List
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from games import threeman

load_dotenv()

TOKEN = os.getenv('DISCORD_APPLICATION_TOKEN')
GAMES_CHANNEL_ID = int(os.getenv('GAMES_CHANNEL_ID'))

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

# Global game state
current_game = None  # Stores the active game instance


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        # Sync commands to Discord
        await tree.sync()
        print("Slash commands synced!")
    except Exception as e:
        print(f"Error syncing slash commands: {e}")


@tree.command(name="start_game", description="Start a game with up to 10 players.")
@app_commands.describe(
    game_name="Name of the game to start",
    player1="First player (required)",
    player2="Second player (required)",
    player3="Third player (optional)",
    player4="Fourth player (optional)",
    player5="Fifth player (optional)",
    player6="Sixth player (optional)",
    player7="Seventh player (optional)",
    player8="Eighth player (optional)",
    player9="Ninth player (optional)",
    player10="Tenth player (optional)"
)
async def start_game(
    interaction: discord.Interaction,
    game_name: str,
    player1: discord.User,
    player2: discord.User,
    player3: discord.User = None,
    player4: discord.User = None,
    player5: discord.User = None,
    player6: discord.User = None,
    player7: discord.User = None,
    player8: discord.User = None,
    player9: discord.User = None,
    player10: discord.User = None
):
    """
    Slash command to start a game with up to 10 players.
    """
    global current_game

    if interaction.channel.id != GAMES_CHANNEL_ID:
        await interaction.response.send_message("Please start the game in the games channel.", ephemeral=True)
        return

    if current_game:
        await interaction.response.send_message(
            f"A game is already in progress: {current_game.name}. Please end it before starting a new one.",
            ephemeral=True,
        )
        return

    # Collect all non-None players into a list
    players = [player for player in [player1, player2, player3, player4, player5, player6, player7, player8, player9, player10] if player]

    if len(players) < 2:
        await interaction.response.send_message(
            "You need to select at least 2 players to start the game.", ephemeral=True
        )
        return

    if game_name.lower() == 'threeman':
        current_game = threeman.ThreeManGame(bot, interaction.channel, players)
    else:
        await interaction.response.send_message(f"Unknown game: {game_name}.", ephemeral=True)
        return

    await current_game.start_game()
    await interaction.response.send_message(
        f"Game {game_name} started with players: {', '.join([player.mention for player in players])}!"
    )


@tree.command(name="end_game", description="End the current game.")
async def end_game(interaction: discord.Interaction):
    global current_game

    if interaction.channel.id != GAMES_CHANNEL_ID:
        await interaction.response.send_message("Please end the game in the general channel.", ephemeral=True)
        return

    if not current_game:
        await interaction.response.send_message("There is no game in progress.", ephemeral=True)
        return

    await current_game.end_game()
    current_game = None
    await interaction.response.send_message("The current game has been ended.")


@tree.command(name="roll", description="Roll the dice during the game.")
async def roll(interaction: discord.Interaction):
    global current_game

    if interaction.channel.id != GAMES_CHANNEL_ID:
        await interaction.response.send_message("Please roll the dice in the general channel.", ephemeral=True)
        return

    if not current_game:
        await interaction.response.send_message("No game is currently running.", ephemeral=True)
        return

    # Delegate to the active game's roll method
    if hasattr(current_game, 'roll'):
        await current_game.roll(interaction)
    else:
        await interaction.response.send_message(
            f"The current game ({current_game.name}) does not support rolling dice.", ephemeral=True
        )


@tree.command(name="hellosgb", description="Say hello to the bot.")
async def hellosgb(interaction: discord.Interaction):
    await interaction.response.send_message("Hello! I am SGB!", ephemeral=True)


# Run the bot
bot.run(TOKEN)
