import discord
from discord.commands import slash_command, Option
from discord.ext import commands

import utils.vote as vt

class Vote(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="vote",description="Create a vote")
    async def vote(self, ctx, timeout_min : Option(int, "幾分鐘後失效 (默認5分鐘)", required = False, default = 5)):
        # Choose vote
        my_vote = vt.DecideVote(ctx.channel, timeout_min, title='Votes')
        await ctx.send_modal(modal=my_vote)

def setup(bot):
    bot.add_cog(Vote(bot))


