# help.py


from utils.info       import silinece_channel

import utils.MusicBot     as my_mb # my class

from discord.commands import slash_command, Option
from discord.ext      import commands

import discord


class Help(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="help",description="Shut me up in this channel")
    async def help(self,ctx):
        await  ctx.respond(""":notes: **MUSIC**
\t - `/play {url}` to play music on youtube.
\t - `/skip` to skip the song.
\t - `/pause` to pause the song.
\t - `/list` to show the playlist
\t - `/loop` to loop current song.
\t - `/clear` to clear the playlist
\t - `/leave` to leave the voice channel.

😆 **CHAT**
\t - `/silence` to shut me up
\t - `/talk` so I can keep talking""")





def setup(bot):
    bot.add_cog(Help(bot))