from utils.info       import silinece_channel

import utils.MusicBot     as my_mb # my class

from discord.commands import slash_command, Option
from discord.ext      import commands

import discord


class Silence(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="silence",description="Shut me up in this channel")
    async def silence(self,ctx):
        silinece_channel.append(ctx.channel.id)

        ctx.respond("ok, I will shut up in this channel :smiling_face_with_tear: :mask: ")


    @slash_command(name="talk",description="Shut me up in this channel")
    async def talk(self,ctx):

        if (ctx.channel.id in silinece_channel):
            silinece_channel.remove(ctx.channel.id)
            ctx.respond(":confetti_ball: Yeah! :confetti_ball:  ")
            return

        ctx.respond("I could have talked.")





def setup(bot):
    bot.add_cog(Silence(bot))