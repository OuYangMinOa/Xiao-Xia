import discord
from discord.commands import slash_command, Option
from discord.ext import commands
import random

class Roll(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name='骰子', description='骰一個數字!')
    async def roll(self,ctx, uppperlimit: Option(int, "上限", required = False, default = 6)):
        
        x = random.randint(1, uppperlimit)
        await ctx.respond(f"You roll {x}!")

def setup(bot):
    bot.add_cog(Roll(bot))