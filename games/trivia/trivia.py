import random

from games.trivia.topics import TRIVIA_TOPICS

class TriviaGame:
    def __init__(self, bot, channel, players, topic, questions):
        self.bot = bot
        self.channel = channel
        self.players = players
        self.topic = topic
        self.questions = questions
        self.used_questions = set()
        self.scores = {player: 0 for player in players}
        self.current_question = None
        self.question_counter = 0

    async def start_game(self):
        await self.channel.send(f"Trivia game started with topic: {self.topic}! Players: {', '.join([player.mention for player in self.players])}")
        await self.ask_question()

    async def ask_question(self):
        # Case when all questions have been asked in a single game
        if len(self.used_questions) == len(self.questions):
            await self.channel.send("All questions have been asked! The game is over.")
            await self.display_leaderboard(final=True)
            return

        # Still questions left, choose random from topic and ask
        self.current_question = random.choice([q for q in self.questions if q not in self.used_questions])
        self.used_questions.add(self.current_question)
        self.question_counter += 1

        await self.channel.send(f"Question {self.question_counter}: {self.current_question['question']}")


    async def handle_answer(self, message):
        # Case when no question is currently being asked
        if not self.current_question:
            return

        correct_answer = self.current_question['answer'].lower()
        if message.content.lower() == correct_answer and message.author in self.players: # Case-insensitive comparison of answers
            self.scores[message.author] += 1
            await self.channel.send(f"{message.author.mention} answered correctly and earns a point!")
            
            if self.question_counter % 5 == 0: # Display leaderboard every 5 questions
                await self.display_leaderboard()

            await self.ask_question() # Ask another question, #TODO: want to implement a delay here


    async def display_leaderboard(self, final=False):
        leaderboard = sorted(self.scores.items(), key=lambda item: item[1], reverse=True)
        leaderboard_message = "\n".join([f"{player.mention}: {score}" for player, score in leaderboard])
        title = "Final Leaderboard:" if final else "Current Leaderboard:"
        await self.channel.send(f"{title}\n{leaderboard_message}")


    async def end_game(self):
        await self.channel.send("Trivia game has been ended prematurely.")
        await self.display_leaderboard(final=True)
