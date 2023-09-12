from discord.commands import slash_command, Option
from discord.ext      import commands

from utils.info       import logger, CheckBool
from utils.info       import music_user, sound_user, Playlist_folder, MUSIC_folder, recording

from utils.PlayListSelection import PlayListSelection

import utils.MusicBot     as my_mb # my class
import threading
import edge_tts
import discord
import asyncio
import os


class Music(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="pause",description="Pause the music")
    async def pause(self,ctx):
        #  await ctx.response.defer( ephemeral=True)

        await ctx.respond("pause" + f' - {ctx.author.mention}')
        voice = ctx.author.voice
        if not voice:
            await ctx.respond("You aren't in a voice channel!")
            return

        if (ctx.channel.id in music_user):
            await music_user[ctx.channel.id].pause()

    @slash_command(name="play",description="play the music (supporting spotify and youtube)")
    async def play(self,ctx,  url: Option(str, "The youtube url", required = False)):
        # await ctx.response.defer( ephemeral=True)

        if (not url):
            await ctx.respond(f'/play\n- {ctx.author.mention}')
        else:
            await ctx.respond(f'{url}\n- {ctx.author.mention}')

        logger.info(f'[*] {url} - {ctx.author.name}')
        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        sound_guild_id = [sound_user[x].ctx.guild.id for x in sound_user]  #  use for check if bot is in the sound dict
        # print(sound_guild_id)

        if (ctx.channel.id in music_user):  #  if bot is in the music dict
            
            if ctx.guild.voice_client not in self.bot.voice_clients:   # in same channel but not in any voice channel
                logger.info("[*] rejoin the voice channel")
                await music_user[ctx.channel.id].kill()
                del music_user[ctx.channel.id]
                voice =  await channel.connect()
                music_user[ctx.channel.id] = my_mb.MusicBot(channel, voice , ctx, self.bot)

            elif (music_user[ctx.channel.id].channelid != channel.id):  # in same channel but not in same voice channel
                await music_user[ctx.channel.id].voice.move_to(channel)
                logger.info(f"[*] move {music_user[ctx.channel.id].channelid} -> {channel.id}")
                music_user[ctx.channel.id].channel    = channel
                music_user[ctx.channel.id].channelid  = channel.id
                music_user[ctx.channel.id].ctx        = ctx

            

            if (not url):
                logger.info("[*] no url specified",music_user[ctx.channel.id].state)

                if (ctx.guild.id in sound_guild_id):  # if bot is in the sound dict
                    sound_channel_id = sound_user[list(sound_user)[sound_guild_id.index(ctx.guild.id)]].ctx.channel.id
                    await sound_user[sound_channel_id].clear()

                if (music_user[ctx.channel.id].state == 2 or music_user[ctx.channel.id].state ==3):
                    await music_user[ctx.channel.id].pause()
                if (music_user[ctx.channel.id].state == 0):
                    await music_user[ctx.channel.id].skip()
            else:
                await music_user[ctx.channel.id].add(url) 
        else:
            try:
                # print("[*] moving to voice channel")
                if (ctx.guild.id in sound_guild_id):  # if bot is in the sound dict
                    # print("[*] moving to voice channel 2222 ")
                    sound_channel_id = sound_user[list(sound_user)[sound_guild_id.index(ctx.guild.id)]].ctx.channel.id # FInd the client channel id
                    # print(sound_channel_id)
                    voice = sound_user[sound_channel_id].voice
                    await sound_user[sound_channel_id].clear()
                else:
                    voice =  await channel.connect()

                ############## Build the Music object 
                # print("[*] voice channel connected")
                MB = my_mb.MusicBot(channel, voice , ctx, self.bot)
                logger.info(f"[*] creating Class id : {id(MB)} for serving channel {channel.id}")
                music_user[ctx.channel.id] = MB
                if (not url):
                    await ctx.send("Use `\play url` to play youtube or spotify music")
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
        # await ctx.response.defer( ephemeral=True)

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
            # await ctx.send("Leaving the voice channel ...")
            await music_user[ctx.channel.id].kill()
            await music_user[ctx.channel.id].voice.disconnect()
            logger.info("[*] leaving  {channel.id}")
            del music_user[ctx.channel.id]


        if (ctx.channel.id in sound_user):  

                # sound_user[ctx.channel.id].crmView.stop()
            for eachctx in sound_user[ctx.channel.id].ctxResArr:
                try:
                    if (isinstance(eachctx,discord.WebhookMessage) or isinstance(eachctx,discord.Message)):
                        await eachctx.delete()
                    else:
                        await eachctx.delete_original_response()
                    sound_user[ctx.channel.id].ctxResArr.remove(eachctx)
                except Exception as e:
                    logger.error(f"[*] Delete original response : {e}")

            # await ctx.send("Leaving the voice channel ...")
            await sound_user[ctx.channel.id].kill()
            await sound_user[ctx.channel.id].voice.disconnect()
            logger.info(f"[*] leaving {channel.id}")
            del sound_user[ctx.channel.id]
            

    @slash_command(name="clear",description="clear the music")
    async def clear(self,ctx):

        # await ctx.response.defer(ephemeral=True)
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
            logger.info(f"[*] Music : {channel.id} cleared")
            await music_user[ctx.channel.id].clear()
        else:
            await ctx.send("I'm not singing")


    @slash_command(name="skip",description="skip the current music")
    async def skip(self,ctx):
        # await ctx.response.defer( ephemeral=True)

        await ctx.respond('skip' + f' - {ctx.author.mention}')

        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        if ctx.guild.voice_client not in self.bot.voice_clients:
            return

        

        if (ctx.channel.id in sound_user):
            await sound_user[ctx.channel.id].skip()
            return 
        
        if (ctx.channel.id in music_user):
            await music_user[ctx.channel.id].skip()
            return

    @slash_command(name="stop_music",description="skip the current music")
    async def stop_music(self,ctx):
        # await ctx.response.defer( ephemeral=True)

        await ctx.respond('stop_music' + f' - {ctx.author.mention}')

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
            return
        
    @slash_command(name="stop_sound",description="skip the current sound")
    async def stop_sound(self,ctx):
        # await ctx.response.defer( ephemeral=True)

        await ctx.respond('stop_sound' + f' - {ctx.author.mention}')

        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        if ctx.guild.voice_client not in self.bot.voice_clients:
            await ctx.send("I'm not singing")
            return
        if (ctx.channel.id in sound_user):
            await sound_user[ctx.channel.id].skip()
            return

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

        # await ctx.response.defer( ephemeral=True)
        logger.info(f'[*] {nums} - {ctx.author.name}')

        await ctx.response.send_message('skipnums' + f' {ctx.author.mention}')


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


    @slash_command(name='save_playlist',description="Save current playlist")
    async def savePlaylist(self,ctx, name : Option(str, "The name of the playlist", required = True)):
        # await ctx.response.defer( ephemeral=True)
        logger.info(f'[*] playlist : {name} - {ctx.author.name} in guild id - {ctx.guild.id}')

        await ctx.respond(f'/save_playlist  - {ctx.author.mention}')
        music_guild_id = [music_user[x].ctx.guild.id for x in music_user]

        if (ctx.guild.id in music_guild_id):
            music_channel_id = music_user[list(music_user)[music_guild_id.index(ctx.guild.id)]].ctx.channel.id
            this_misuser = music_user[music_channel_id]
            thisPlaylist = this_misuser.passed + this_misuser.queqed
            if (len(thisPlaylist)==0):
                await ctx.send(f"Playlist is empty")
                logger.info(f"[*] playlist is empty")
                return
            
            guildPlaylistFolder = os.path.join(Playlist_folder,f"{ctx.guild.id}")
            os.makedirs(Playlist_folder    , exist_ok=True)
            os.makedirs(guildPlaylistFolder, exist_ok=True)

            Playlist_filename = os.path.join(guildPlaylistFolder,f"{name}.txt")
            msg = ""
            for title,url in thisPlaylist:
                msg = msg + f"{title},{url}\n"
            with open(Playlist_filename,"w",encoding='utf-8') as f:
                f.write(msg.strip())

            await ctx.send(f"Playlist {name} saved, use `/playlist` to check it.")
            logger.info(f"[*] playlist save in {Playlist_filename}")
        else:
            await ctx.send(f"I not even in the vocie channel...")
            logger.info(f"[*] Not in the voice channel")

    @slash_command(name="playlist",description="list all the playlist")
    async def playlist(self,ctx):

        # for _ in range(10):
        #     try:
        #         await ctx.response.defer(ephemeral=True)
        #         await ctx.respond(f'playlist - {ctx.author.mention}')
        #         break
        #     except:
        #         print("[*] retrying...")

        # await ctx.response.defer( ephemeral=True)
        logger.info(f'[*] load_playlist - {ctx.guild.id}')
        await ctx.respond(f'playlist - {ctx.author.mention}')
        


        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        sound_guild_id = [sound_user[x].ctx.guild.id for x in sound_user]


        if (ctx.channel.id in music_user):
            if ctx.guild.voice_client not in self.bot.voice_clients:   # in same channel but not in any voice channel
                await music_user[ctx.channel.id].kill()
                del music_user[ctx.channel.id]
                logger.info("[*] rejoin the voice channel")
                voice =  await channel.connect()
                music_user[ctx.channel.id] = my_mb.MusicBot(channel, voice , ctx, self.bot)

            if (music_user[ctx.channel.id].channelid != channel.id):  # in same channel but not in same voice channel
                await music_user[ctx.channel.id].voice.move_to(channel)
                logger.info(f"[*] move {music_user[ctx.channel.id].channelid} -> {channel.id}")
                music_user[ctx.channel.id].channel    = channel
                music_user[ctx.channel.id].channelid  = channel.id
                music_user[ctx.channel.id].ctx        = ctx
        else:
            if (ctx.guild.id in sound_guild_id):
                    sound_channel_id = sound_user[list(sound_user)[sound_guild_id.index(ctx.guild.id)]].ctx.channel.id
                    voice = sound_user[sound_channel_id].voice
                    await sound_user[sound_channel_id].clear()
            else:
                voice =  await channel.connect()
            MB = my_mb.MusicBot(channel, voice , ctx, self.bot)
            logger.info(f"[*] creating Class id : {id(MB)} for serving channel {channel.id}")
            music_user[ctx.channel.id] = MB

        guildPlaylistFolder = os.path.join(Playlist_folder,f"{ctx.guild.id}")
        

        PLS = PlayListSelection(music_user[ctx.channel.id],guildPlaylistFolder)

        if (len(PLS.label) == 0):
            await ctx.respond(f'No playlist found.')
        else:
            await ctx.respond(f"Available playlist", view=PLS.view)


    @slash_command(name="say",description="Let me say something")
    async def say(self,ctx, word:Option(str,"THe word you want me to say",required=True)):
        # await ctx.response.defer( ephemeral=True)
        logger.info(f'[*] {ctx.author.name} - {word}')

        await ctx.respond(f'[*] say - {ctx.author.name}\n{word}',ephemeral=True)

        if not ctx.author.voice:
            await ctx.send('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        sound_guild_id = [sound_user[x].ctx.guild.id for x in sound_user]  #  use for check if bot is in the sound dict


        if (ctx.channel.id in music_user):  #  if bot is in the music dict
            
            if ctx.guild.voice_client not in self.bot.voice_clients:   # in same channel but not in any voice channel
                logger.info("[*] rejoin the voice channel")
                await music_user[ctx.channel.id].kill()
                del music_user[ctx.channel.id]
                voice =  await channel.connect()
                music_user[ctx.channel.id] = my_mb.MusicBot(channel, voice , ctx, self.bot)

            elif (music_user[ctx.channel.id].channelid != channel.id):  # in same channel but not in same voice channel
                await music_user[ctx.channel.id].voice.move_to(channel)
                logger.info(f"[*] move {music_user[ctx.channel.id].channelid} -> {channel.id}")
                music_user[ctx.channel.id].channel    = channel
                music_user[ctx.channel.id].channelid  = channel.id
                music_user[ctx.channel.id].ctx        = ctx


        else:
            try:
                if (ctx.guild.id in sound_guild_id):  # if bot is in the sound dict
                    sound_channel_id = sound_user[list(sound_user)[sound_guild_id.index(ctx.guild.id)]].ctx.channel.id # FInd the client channel id
                    voice = sound_user[sound_channel_id].voice
                    await sound_user[sound_channel_id].clear()
                else:
                    voice =  await channel.connect()
                ############## Build the Music object 
                MB = my_mb.MusicBot(channel, voice , ctx, self.bot)
                logger.info(f"[*] creating Class id : {id(MB)} for serving channel {channel.id}")
                music_user[ctx.channel.id] = MB
            except Exception as e:
                logger.error(e)



        logger.info(f"[*] creating sound .... ")
        os.makedirs(MUSIC_folder,exist_ok=True)
        filename = f"{MUSIC_folder}//{ctx.guild.id}.mp3"

        ## say something
        VOICE = "zh-CN-YunxiNeural"
        communicate = edge_tts.Communicate(word, VOICE,rate= "-5%",volume="+20%")
        await communicate.save(filename)

        logger.info(f"[*] Build sound successful !!")


        lastMusicTime = music_user[ctx.channel.id].startTime
        await music_user[ctx.channel.id].pause("(Stop cause I'm saying something)")

        tempqueqe = music_user[ctx.channel.id].queqed
        temppasse = music_user[ctx.channel.id].passed

        music_user[ctx.channel.id].passed = []
        music_user[ctx.channel.id].queqed = [ (f"{ctx.guild.id}.mp3",""),]
        logger.info(f"[*] Try to play sound .... ")


        await music_user[ctx.channel.id]._next()

        while music_user[ctx.channel.id].StartCount:   
            await asyncio.sleep(1)

        music_user[ctx.channel.id].startTime = lastMusicTime

        music_user[ctx.channel.id].state = 3
        music_user[ctx.channel.id].queqed = tempqueqe
        music_user[ctx.channel.id].passed = temppasse
        await music_user[ctx.channel.id].pause()

        


        
def setup(bot):
    bot.add_cog(Music(bot))



    