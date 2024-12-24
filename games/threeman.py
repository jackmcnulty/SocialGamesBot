import random
import discord
from discord.ext import commands

class ThreeManGame:
    def __init__(self, bot, channel, players):
        self.bot = bot
        self.channel = channel
        self.players = list(players)
        self.threeman = None
        self.threeman_skipped = False
        self.roller = None
        self.started = False
        self.rules = self._initialize_rules()


    def name(self):
        return "Threeman"


    def _initialize_rules(self):
        """Initialize the list of rules."""
        return [
            {
                "name": "threeman_drink",
                "condition": lambda die1, die2, total: 3 in [die1, die2, total],
                "action": self.rule_threeman_drink,
            },
            {
                "name": "double_ones",
                "condition": lambda die1, die2, total: die1 == 1 and die2 == 1,
                "action": self.rule_double_ones,
            },
            {
                "name": "double_twos",
                "condition": lambda die1, die2, total: die1 == 2 and die2 == 2,
                "action": self.rule_double_twos,
            },
            {
                "name": "double_threes",
                "condition": lambda die1, die2, total: die1 == 3 and die2 == 3,
                "action": self.rule_double_threes,
            },
            {
                "name": "double_fours",
                "condition": lambda die1, die2, total: die1 == 4 and die2 == 4,
                "action": self.rule_double_fours,
            },
            {
                "name": "double_fives",
                "condition": lambda die1, die2, total: die1 == 5 and die2 == 5,
                "action": self.rule_double_fives,
            },
            {
                "name": "double_sixes",
                "condition": lambda die1, die2, total: die1 == 6 and die2 == 6,
                "action": self.rule_double_sixes,
            },
            {
                "name": "everyone_drinks",
                "condition": lambda die1, die2, total: (die1, die2) in [(4, 1), (4, 6), (1, 4), (6, 4)],
                "action": self.rule_everyone_drinks,
            },
            {
                "name": "total_seven",
                "condition": lambda die1, die2, total: total == 7,
                "action": self.rule_total_seven,
            },
            {
                "name": "total_eleven",
                "condition": lambda die1, die2, total: total == 11,
                "action": self.rule_total_eleven,
            },
        ]


    async def rule_threeman_drink(self, ctx, die1, die2, total):
        """Rule: Threeman drinks for each 3 rolled."""
        drinks = [die for die in [die1, die2] if die == 3]
        if drinks:
            await self.channel.send(f"The Threeman ({self.threeman}) drinks {len(drinks)} times!")


    async def rule_double_ones(self, ctx, die1, die2, total):
        """Rule: Double ones."""
        await self.channel.send(f"{self.roller} rolled double ones! Tell anyone to finish their drink.")


    async def rule_double_twos(self, ctx, die1, die2, total):
        """Rule: Double twos."""
        await self.channel.send(f"{self.roller} rolled double twos! Give out 8 drinks.")


    async def rule_double_threes(self, ctx, die1, die2, total):
        """Rule: Double threes."""
        await self.channel.send(f"{self.roller} rolled double threes! Give out 6 drinks.")


    async def rule_double_fours(self, ctx, die1, die2, total):
        """Rule: Double fours."""
        await self.channel.send(f"{self.roller} rolled double fours! Give out 8 drinks.")


    async def rule_double_fives(self, ctx, die1, die2, total):
        """Rule: Double fives."""
        await self.channel.send(f"{self.roller} rolled double fives! Give out 10 drinks.")


    async def rule_double_sixes(self, ctx, die1, die2, total):
        """Rule: Double sixes."""
        await self.channel.send(f"{self.roller} rolled double sixes! Give out 12 drinks.")


    async def rule_everyone_drinks(self, ctx, die1, die2, total):
        """Rule: Everyone drinks."""
        await self.channel.send("Everyone drinks!")


    async def rule_total_seven(self, ctx, die1, die2, total):
        """Rule: Total of 7."""
        index = (self.players.index(self.roller) - 1) % len(self.players)
        await self.channel.send(f"Total of 7! {self.players[index]} drinks.")


    async def rule_total_eleven(self, ctx, die1, die2, total):
        """Rule: Total of 11."""
        index = (self.players.index(self.roller) + 1) % len(self.players)
        await self.channel.send(f"Total of 11! {self.players[index]} drinks.")


    async def apply_rules(self, ctx, die1, die2, total):
        """Apply all applicable rules to the roll."""
        any_rule_applied = False

        for rule in self.rules:
            if rule['condition'](die1, die2, total):
                await rule['action'](ctx, die1, die2, total)
                any_rule_applied = True

        return any_rule_applied


    async def roll(self, interaction: discord.Interaction):
        if not self.started:
            await interaction.response.send_message("The game has not started yet.", ephemeral=True)
            return

        if interaction.user != self.roller:
            await interaction.response.send_message(
                f"It's not your turn, {interaction.user.mention}! Wait for {self.roller.mention} to roll.", ephemeral=True
            )
            return

        # Defer the interaction to prevent timeouts and allow multiple follow-up messages
        await interaction.response.defer()

        if self.threeman == self.roller and not self.threeman_skipped:
            # Skip the Threeman's turn once
            self.threeman_skipped = True
            await interaction.followup.send(
                f"{self.roller.mention} is the Threeman and gets skipped this round. Passing to the next player."
            )
            current_index = self.players.index(self.roller)
            next_index = (current_index + 1) % len(self.players)
            self.roller = self.players[next_index]
            await interaction.followup.send(f"It's now {self.roller.mention}'s turn!")
            return

        die1, die2 = random.randint(1, 6), random.randint(1, 6)
        total = die1 + die2
        await interaction.followup.send(f"{self.roller.mention} rolled a {die1} and a {die2} (Total: {total}).")

        if self.threeman is None:
            # Threeman is unassigned
            if 3 in [die1, die2, total]:
                self.threeman = self.roller
                await interaction.followup.send(f"{self.roller.mention} rolled a 3 and is now the Threeman! Drink up!")
                # Move to the next player after assigning the Threeman
                current_index = self.players.index(self.roller)
                next_index = (current_index + 1) % len(self.players)
                self.roller = self.players[next_index]
                await interaction.followup.send(f"It's now {self.roller.mention}'s turn!")
                return

        if self.threeman == self.roller:
            # Threeman is rolling out
            if 3 in [die1, die2, total]:
                await interaction.followup.send(
                    f"{self.roller.mention} rolled a 3 and is no longer the Threeman! The position is now open."
                )
                self.threeman = None
                self.threeman_skipped = False  # Reset skip tracking
                # Next player rolls for Threeman
                current_index = self.players.index(self.roller)
                next_index = (current_index + 1) % len(self.players)
                self.roller = self.players[next_index]
                await interaction.followup.send(f"The Threeman position is open! {self.roller.mention}, roll to claim it!")
                return

        # Apply rules for the current roll
        if not await self.apply_rules(interaction, die1, die2, total):
            await interaction.followup.send(f"No rule matched. {self.roller.mention}'s turn ends.")

            # Move to the next player
            current_index = self.players.index(self.roller)
            next_index = (current_index + 1) % len(self.players)
            self.roller = self.players[next_index]
            await interaction.followup.send(f"It's now {self.roller.mention}'s turn!")
        else:
            # Inform the roller to roll again if rules matched
            await interaction.followup.send(f"{self.roller.mention}, it's still your turn! Roll again with `/roll`.")



    async def start_game(self):
        if len(self.players) < 2:
            await self.channel.send("You need at least 2 players to start a game of Threeman.")
            return

        # Randomly select the first roller
        self.roller = random.choice(self.players)
        self.started = True

        player_mentions = ", ".join(player.mention for player in self.players)
        await self.channel.send(f"Starting a game of Threeman with players: {player_mentions}.")
        await self.channel.send(f"{self.roller.mention} is the first roller! Roll the dice with `!roll`. The threeman is open.")


    async def end_game(self):
        self.started = False
        self.threeman = None
        self.roller = None

        await self.channel.send("The game of Threeman has ended. Thanks for playing!")


