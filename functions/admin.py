from utils.info       import logger
from discord.commands import slash_command, Option
from discord.ext      import commands
from glob             import glob
from main             import RestartBot
from utils.info       import recording, music_user, sound_user

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
            for eachKey in music_user.copy():
                try:
                    await  music_user[eachKey].kill()
                except:
                    pass 
            for eachKey in sound_user.copy():
                try:
                    await  sound_user[eachKey].kill()
                except:
                    pass 
            for eachKey in recording.copy():
                try:
                    await  recording[eachKey].kill()
                except:
                    pass 

        else:
            await ctx.respond("Permission denied",ephemeral=True)

    @slash_command(name="keep_alive",description="Keep my bot alive")
    async def keep_alive(self, ctx, password: Option(str, "password", required = True)):
        if ( str(os.getenv('RESTART_PASS'))==password):
            while True:
                await ctx.respond("I'm alive",delete_after=5)
                await asyncio.sleep(8)
        else:
            await ctx.respond("Permission denied",ephemeral=True)

def setup(bot):
    bot.add_cog(admin(bot))