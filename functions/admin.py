from utils.info       import logger
from discord.commands import slash_command, Option
from discord.ext      import commands
from glob             import glob
from main             import RestartBot
import discord
import os


class admin(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="reboot",description="重新啟動")
    async def reboot(self, ctx, password: Option(str, "password", required = True)):
        if ( str(os.getenv('RESTART_PASS'))==password):
            await ctx.respond("Restarting...",ephemeral=True)
        else:
            await ctx.respond("Permission denied",ephemeral=True)



def setup(bot):
    bot.add_cog(admin(bot))