from utils.info       import silinece_channel, Silence_DATA, logger

import utils.MusicBot     as my_mb # my class

from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.file_os import *
import discord


class Silence(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="silence",description="Shut me up in this channel")
    async def silence(self,ctx):
        try:
            if (ctx.channel.id not in silinece_channel):
                silinece_channel.append(ctx.channel.id)
                addtxt(Silence_DATA,ctx.channel.id)
            await ctx.respond("ok, I will shut up in this channel :smiling_face_with_tear: :mask:")
        except Exception as e:
            logger.error(e)


    @slash_command(name="talk",description="Shut me up in this channel")
    async def talk(self,ctx):
        try:
            if (ctx.channel.id in silinece_channel):
                silinece_channel.remove(ctx.channel.id)
                newtxt(Silence_DATA, silinece_channel)
                await ctx.respond(":confetti_ball: Yeah! :confetti_ball:  ")
                return

            await ctx.respond("I could have talked.")
        except Exception as e:
            logger.error(e)





def setup(bot):
    bot.add_cog(Silence(bot))