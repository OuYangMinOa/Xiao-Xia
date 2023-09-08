from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.check      import RestartBot
from utils.info       import music_user
from utils.info       import sound_user
from utils.info       import recording
from utils.info       import CheckBool
from utils.info       import logger
from datetime         import datetime
from glob             import glob

import discord
import asyncio
import os


class admin(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="reboot",description="重新啟動")
    async def reboot(self, ctx, password: Option(str, "password", required = True)):
        if ( str(os.getenv('RESTART_PASS'))==password):
            await ctx.respond("Restarting...",ephemeral=True)
            await RestartBot(self.bot)
        else:
            await ctx.respond("Permission denied",ephemeral=True)

    @slash_command(name="keep_alive",description="Keep my bot alive")
    async def keep_alive(self, ctx, password: Option(str, "password", required = True)):
        if ( str(os.getenv('RESTART_PASS'))==password):
            NowTime = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
            await ctx.respond(f"I'm alive  ({NowTime})",delete_after=5)
            while True:
                NowTime = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
                await ctx.channel.send(f"I'm alive  ({NowTime})",delete_after=5)
                await asyncio.sleep(5.1)
        else:
            await ctx.respond("Permission denied",ephemeral=True)

def setup(bot):
    bot.add_cog(admin(bot))