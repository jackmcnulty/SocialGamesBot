import random
import asyncio

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
        self.lock = asyncio.Lock()
        self.question_active = False 

    async def start_game(self):
        await self.channel.send("Starting trivia game in 5 seconds!")
        await asyncio.sleep(5)
        await self.ask_question()

    async def ask_question(self):
        # Case when all questions have been asked
        if len(self.used_questions) == len(self.questions):
            await self.channel.send("All questions have been asked! The game is over.")
            await self.display_leaderboard(final=True)
            return

        # Select a random question that hasn't been asked
        available_questions = [q for q in self.questions if q['question'] not in self.used_questions]
        if not available_questions:
            await self.channel.send("All questions have been asked! The game is over.")
            await self.display_leaderboard(final=True)
            return

        self.current_question = random.choice(available_questions)
        self.used_questions.add(self.current_question['question'])  # Mark this question as used
        self.question_counter += 1
        self.question_active = True  # Allow players to answer

        # Prepend the topic in bold if 'all_topics' is selected
        if self.topic == "all_topics":
            question_text = f"**[{self.current_question['topic'].capitalize()}]** {self.current_question['question']}"
        else:
            question_text = self.current_question['question']

        await self.channel.send(f"Question {self.question_counter}: {question_text}")

    async def handle_answer(self, message):
        """
        Checks if a user's message matches the correct answer.
        """
        async with self.lock:  # Prevent race conditions with multiple answers
            if not self.current_question or not self.question_active:
                return  # No question is active or question has been answered

            correct_answer = self.current_question['answer'].strip().lower()
            if message.content.strip().lower() == correct_answer and message.author in self.players:
                self.scores[message.author] += 1
                self.question_active = False  # Disable further answers for this question
                await self.channel.send(f"{message.author.mention} answered correctly and earns a point!")

                # Every 5 questions, show the leaderboard
                if self.question_counter % 5 == 0:
                    await self.display_leaderboard()
                    await asyncio.sleep(8)  # Longer delay after leaderboard
                    await self.channel.send("Next question coming up...")
                    await asyncio.sleep(2)
                else:
                    await asyncio.sleep(4)  # Shorter delay between regular questions
                    await self.channel.send("Next question coming up...")
                    await asyncio.sleep(2)


                await self.ask_question()  # Ask the next question

    async def idk(self):
        """
        Reveal the answer to the current question and move on.
        """
        async with self.lock:  # Locking to ensure only one action is processed
            # Check if the question is active
            if not self.current_question or not self.question_active:
                await self.channel.send("No active question to skip.")
                return

            # Reveal the answer and disable the current question
            self.question_active = False  # Disable further actions for this question
            answer = self.current_question['answer']
            await self.channel.send(f"The correct answer was: **{answer}**. Nobody earns a point.")

            # Delay before moving to the next question
            await asyncio.sleep(4)
            # Add a chat countdown before the next question
            await self.channel.send("Next question coming up...")
            await asyncio.sleep(2)
            await self.ask_question()

    async def display_leaderboard(self, final=False):
        """
        Display the leaderboard, either as a final summary or current standings.
        """
        leaderboard = sorted(self.scores.items(), key=lambda item: item[1], reverse=True)
        leaderboard_message = "\n".join([f"{player.mention}: {score}" for player, score in leaderboard])
        title = "Final Leaderboard:" if final else "Current Leaderboard:"
        await self.channel.send(f"{title}\n{leaderboard_message}")

    async def end_game(self):
        """
        Ends the game prematurely and displays the final leaderboard.
        """
        await self.channel.send("Trivia game has been ended prematurely.")
        await self.display_leaderboard(final=True)
