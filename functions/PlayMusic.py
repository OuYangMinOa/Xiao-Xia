from discord.commands import slash_command, Option
from discord.ext      import commands

from utils.info     import logger
from utils.info       import music_user, sound_user

import utils.MusicBot     as my_mb # my class
import discord



class Music(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="pause",description="Pause the music")
    async def pause(self,ctx):
        await ctx.respond("pause" + f' - {ctx.author.mention}')
        voice = ctx.author.voice
        if not voice:
            await ctx.respond("You aren't in a voice channel!")
            return

        if (ctx.channel.id in music_user):
            await music_user[ctx.channel.id].pause()

    @slash_command(name="play",description="play the music")
    async def play(self,ctx,  url: Option(str, "The youtube url", required = False)):
        if (not url):
            await ctx.respond(f'/play\n- {ctx.author.mention}')
        else:
            await ctx.respond(f'{url}\n- {ctx.author.mention}')

        logger.info(f'{url} - {ctx.author.mention}')
        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel
        if (ctx.channel.id in music_user):
            if (music_user[ctx.channel.id].channelid != channel.id):  # in same channel but not in same voice channel
                await music_user[ctx.channel.id].voice.move_to(channel)
                logger.info(f"[*] move {music_user[ctx.channel.id].channelid} -> {channel.id}")
                music_user[ctx.channel.id].channel    = channel
                music_user[ctx.channel.id].channelid  = channel.id
                music_user[ctx.channel.id].ctx        = ctx

            if ctx.guild.voice_client not in self.bot.voice_clients:   # in same channel but not in any voice channel
                await music_user[ctx.channel.id].kill()
                del music_user[ctx.channel.id]
                logger.info("[*] rejoin the voice channel")
                voice =  await channel.connect()
                music_user[ctx.channel.id] = my_mb.MusicBot(channel, voice , ctx, self.bot)

            if (not url):
                print("[*] no url specified",music_user[ctx.channel.id].state)

                if (ctx.channel.id in sound_user):
                    await sound_user[ctx.channel.id].clear()

                if (music_user[ctx.channel.id].state == 2 or music_user[ctx.channel.id].state ==3):
                    await music_user[ctx.channel.id].pause()
                if (music_user[ctx.channel.id].state == 0):
                    await music_user[ctx.channel.id].skip()
            else:
                await music_user[ctx.channel.id].add(url) 
        else:
            try:
                print("[*] moving to voice channel")
                if (ctx.channel.id in sound_user):
                    voice = sound_user[ctx.channel.id].voice
                    await sound_user[ctx.channel.id].clear()
                else:
                    voice =  await channel.connect()
                print("[*] voice channel connected")
                MB = my_mb.MusicBot(channel, voice , ctx, self.bot)
                logger.info(f"[*] creating Class id : {id(MB)} for serving channel {channel.id}")
                music_user[ctx.channel.id] = MB
                if (not url):
                    await ctx.send("Use `\play url` to play youtube music")
                else:
                    await MB.add(url)
            except Exception as e:
                logger.error(e)
                

    @slash_command(name="list",description="List all the music")
    async def list(self,ctx):
        await ctx.respond( f'list - {ctx.author.mention}')


        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        if ctx.guild.voice_client not in self.bot.voice_clients:
            await ctx.send("I'm not singing")
            return

        if (ctx.channel.id in music_user):
            logger.info(f"[*] {channel.id} is asking the playlist")
            await music_user[ctx.channel.id].list()
            # await ctx.send(f"Total {len(self.queqed)} songs")

    @slash_command(name="leave",description="leave the voice channel")
    async def leave(self,ctx):
        await ctx.respond('leave' + f' - {ctx.author.mention}')


        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel
        if ctx.guild.voice_client not in self.bot.voice_clients:
            await ctx.send("I already leaved ...")
            return
        if (ctx.channel.id in music_user):
            await ctx.send("Leaving the voice channel ...")
            await music_user[ctx.channel.id].kill()
            await music_user[ctx.channel.id].voice.disconnect()
            logger.info("[*] leaving", channel.id)
            del music_user[ctx.channel.id]

    @slash_command(name="clear",description="clear the music")
    async def clear(self,ctx):

        await ctx.respond('clear' + f' - {ctx.author.mention}' )


        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        if ctx.guild.voice_client not in self.bot.voice_clients:
            await ctx.send("I'm not singing")
            return

        if (ctx.channel.id in music_user):
            logger.info(f"[*] {channel.id} cleared")
            await music_user[ctx.channel.id].clear()
        else:
            await ctx.send("I'm not singing")

    @slash_command(name="skip",description="skip the current music")
    async def skip(self,ctx):

        await ctx.respond('skip' + f' - {ctx.author.mention}')


        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        if ctx.guild.voice_client not in self.bot.voice_clients:
            await ctx.send("I'm not singing")
            return

        if (ctx.channel.id in music_user):
            await music_user[ctx.channel.id].skip()
        else:
            await ctx.send("I'm not singing")

    @slash_command(name="loop",description="loop the music list")
    async def loop(self,ctx):
        await ctx.respond('loop'  + f' - {ctx.author.mention}')

        
        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        if ctx.guild.voice_client not in self.bot.voice_clients:
            await ctx.send("I'm not singing")
            return

        if (ctx.channel.id in music_user):
            if (not music_user[ctx.channel.id].loop):
                music_user[ctx.channel.id].loop = True
                await ctx.send("looping right now")
                if (music_user[ctx.channel.id].state == 0):
                    await music_user[ctx.channel.id].skip()
            else:
                music_user[ctx.channel.id].loop = False
                await ctx.send("disable loop")


    @slash_command(name="skipnums",description="skip the current music")
    async def skipnums(self,ctx,  nums: Option(int, "The number of music you want to skip", required = True)):

        await ctx.respond('skipnums' + f' - {ctx.author.mention}')


        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        if ctx.guild.voice_client not in self.bot.voice_clients:
            await ctx.send("I'm not singing")
            return

        if (ctx.channel.id in music_user):
            await music_user[ctx.channel.id].skipnums(nums)
        else:
            await ctx.send("I'm not singing")


def setup(bot):
    bot.add_cog(Music(bot))