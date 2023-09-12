from discord.commands import slash_command, Option
from discord.ext      import commands
from utils.info       import logger
from utils.info       import sound_user, music_user, recording
from glob             import glob
from pydub            import AudioSegment


import utils.MusicBot     as my_mb # my class
import discord
import asyncio
import os


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


class Sounds(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command( name="upload_sound",description="upload sound file")
    async def upload_sound(self,ctx, filename : Option(str, "The name of the sound", required = True), file: discord.Attachment):
        for _ in range(10):
            try:
                # await ctx.response.defer()
                await ctx.respond(f"/upload_sound - {ctx.author.mention}",ephemeral=True,delete_after=10)
                break
            except:
                print("[*] retrying...")

        logger.info(f"upload_sound {ctx.author.name}")


        if file:
        # Check if there are any attachments
            attachment = file

            if ( not attachment.filename.endswith('mp3') and not attachment.filename.endswith('wav')):
                await ctx.respond(f"Only allow mp3 and wav files")
                return
            
            file_extend = "mp3" if attachment.filename.endswith('mp3') else "wav"

            save_folder = f"data/attachments/{ctx.guild.id}"
            os.makedirs(save_folder,exist_ok=True)
            await attachment.save(f"{save_folder}/{filename}.{file_extend}") 

            await ctx.respond(f"{filename}.{file_extend} received.")
            logger.info(f"[*] {filename}.{file_extend} received."+ f' - {ctx.author.name}')


            ####  re normalize the attachment file dfbs
            try:
                sound = AudioSegment.from_file(f"{save_folder}/{filename}.{file_extend}")
                normalized_sound = match_target_amplitude(sound, -20.0)
                normalized_sound.export(f"{save_folder}/{filename}.{file_extend}")
            except:
                logger.error("[*] Normalize goes wrong")



        else:
            await ctx.respond("No file attached.")

    @slash_command(name="list_sound",description="list all the sounds in this channel")
    async def list_sound(self,ctx):
        print(ctx.response.is_done())
        
        

        ThisRespond = await ctx.respond(f"/list_sound - {ctx.author.mention}",delete_after=10)
        logger.info(f"list_sound {ctx.author.name}")


        ##  connect to a voice channel
        try:
            if not ctx.author.voice:
                await ctx.respond('you are not connected to a voice channel')
                return
            else:
                channel = ctx.author.voice.channel

            music_user_guild = [music_user[x].ctx.guild.id for x in music_user]  # store all guild in music_user

            if (ctx.channel.id in sound_user):  # in sound_user
                if ctx.guild.voice_client not in self.bot.voice_clients:   # in music_user but not in any voice channel
                    await sound_user[ctx.channel.id].kill()
                    del sound_user[ctx.channel.id]
                    logger.info("[*] rejoin the voice channel")
                    voice =  await channel.connect()
                    sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)
                elif (sound_user[ctx.channel.id].channelid != channel.id):  # in same channel but not in same voice channel
                    await sound_user[ctx.channel.id].voice.move_to(channel)
                    logger.info(f"[*] move {sound_user[ctx.channel.id].channelid} -> {channel.id}")
                    sound_user[ctx.channel.id].channel    = channel
                    sound_user[ctx.channel.id].channelid  = channel.id
                    sound_user[ctx.channel.id].ctx        = ctx

            elif (ctx.guild.id in music_user_guild):  # in music_user (a simple transfer)
                music_channel_id = music_user[list(music_user)[music_user_guild.index(ctx.guild.id)]].ctx.channel.id


                if (music_user[music_channel_id].channelid != channel.id):
                    await music_user[music_channel_id].voice.move_to(channel)
                    logger.info(f"[*]  music_user : {music_user[music_channel_id].channelid} -> sound_user : {channel.id}")

                sound_user[ctx.channel.id] = SoundBot(channel, music_user[music_channel_id].voice , ctx, self.bot)

                if ctx.guild.voice_client not in self.bot.voice_clients:
                    await music_user[music_channel_id].kill()
                    # del music_user[ctx.channel.id]
                    logger.info("[*] rejoin the voice channel")
                    voice =  await channel.connect()
                    sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)
            else:
                print("[*] moving to voice channel")
                voice =  await channel.connect()
                print("[*] voice channel connected")
                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)

            CRM = BuildSoundSelect(ctx.guild.id, sound_user[ctx.channel.id])

            if (len(CRM.label)==0):
                await ctx.respond("you haven't upload any sound files")
                return
            
            logger.info(f"[*] list sound"+ f' - {ctx.author.name}')

            # ThisRespond
            sound_user[ctx.channel.id].ctxResArr.append(ThisRespond)


            ctxResMess =  await ctx.respond(f"Available sound (total:{CRM.count})")
            sound_user[ctx.channel.id].ctxResArr.append(ctxResMess)

            thisCount = 1
            for eachView in CRM.views:
                ctxRes =  await ctx.send(f"({thisCount}/{len(CRM.views)})",view=eachView)
                sound_user[ctx.channel.id].ctxResArr.append(ctxRes)
                print(type(ctxRes))
                thisCount += 1

            

        except Exception as e:
            logger.error(e)


    @slash_command( name="search_sound",description="Search sound file")
    async def search_sound(self,ctx, keyword:Option(str, "The keywords", required = True)):
        
        # await ctx.response.defer( ephemeral=True)
        ThisRespond = await ctx.respond(f"/search_sound - {ctx.author.mention}",ephemeral=True)
        
        if not ctx.author.voice:
            await ctx.respond('you are not connected to a voice channel')
            return
        else:
            channel = ctx.author.voice.channel

        music_user_guild = [music_user[x].ctx.guild.id for x in music_user]  # store all guild in music_user

        if (ctx.channel.id in sound_user):  # in sound_user
            if ctx.guild.voice_client not in self.bot.voice_clients:   # in music_user but not in any voice channel
                await sound_user[ctx.channel.id].kill()
                del sound_user[ctx.channel.id]
                logger.info("[*] rejoin the voice channel")
                voice =  await channel.connect()
                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)

            elif (sound_user[ctx.channel.id].channelid != channel.id):  # in same channel but not in same voice channel
                await sound_user[ctx.channel.id].voice.move_to(channel)
                logger.info(f"[*] move {sound_user[ctx.channel.id].channelid} -> {channel.id}")
                sound_user[ctx.channel.id].channel    = channel
                sound_user[ctx.channel.id].channelid  = channel.id
                sound_user[ctx.channel.id].ctx        = ctx

            

        elif (ctx.guild.id in music_user_guild):  # in music_user (a simple transfer)
            music_channel_id = music_user[list(music_user)[music_user_guild.index(ctx.guild.id)]].ctx.channel.id


            if ctx.guild.voice_client not in self.bot.voice_clients:   
                await music_user[ctx.channel.id].kill()
                # del music_user[ctx.channel.id]
                logger.info("[*] rejoin the voice channel")
                voice =  await channel.connect()
                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)


            elif (music_user[music_channel_id].channelid != channel.id):  # in same channel but not in same voice channel
                await music_user[music_channel_id].voice.move_to(channel)
                logger.info(f"[*]  music_user : {music_user[music_channel_id].channelid} -> sound_user : {channel.id}")
                sound_user[music_channel_id] = SoundBot(channel, music_user[music_channel_id].voice , ctx, self.bot)

                # del music_user[ctx.channel.id]

            
        else:
            print("[*] moving to voice channel")
            voice =  await channel.connect()
            print("[*] voice channel connected")
            sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)

        save_folder = os.path.join("data/attachments", str(ctx.guild.id))
        label, file = [], []
        for path in glob(f'{save_folder}/*.*'):
            if ( (path.endswith('mp3') or path.endswith('wav')) and keyword in path):
                label.append(os.path.basename(path[:-4]))
                file.append( os.path.basename(path) )

        options = [ discord.SelectOption(label=label[i])for i in range(len(label))]
        view = discord.ui.View(timeout=24*60*60)
        for i in range(len(options)//24+1):
            if (len(label[24*(i):24*(i+1)])!=0):
                this_select = MySelection(sound_user[ctx.channel.id],label[24*(i):24*(i+1)] ,file[24*(i):24*(i+1)] ).select
                view.add_item(this_select)

        if (len(label)==0):
            await ctx.respond("Sound files no found", ephemeral=True)
            return
        logger.info(f"[*] search sound"+ f'{keyword}  - {ctx.author.name}')
        
        ctxRes = await ctx.respond(f"Keyword : {keyword}", view=view, ephemeral=True)
        sound_user[ctx.channel.id].ctxResArr.append(ctxRes)
        # ThisRespond
        sound_user[ctx.channel.id].ctxResArr.append(ThisRespond)


class SoundBot(my_mb.MusicBot):
    def __init__(self,channel, voice , ctx, client):
        super().__init__(channel, voice , ctx, client)
        self.floder = f"data/attachments/{ctx.guild.id}"
        self.loop   = False

    async def playSound(self,thisFile):
        await self.clear()
        self.queqed = [(thisFile,''), ]

        music_user_guild = [music_user[x].ctx.guild.id for x in music_user]  # store all guild in music_user


        ## check if any music playing on that guild
        if (self.ctx.guild.id  in music_user_guild):
            music_channel_id = music_user[list(music_user)[music_user_guild.index(self.ctx.guild.id)]].ctx.channel.id
            if (music_user[music_channel_id].state == 1):
                lastMusicTime = music_user[music_channel_id].startTime
                await music_user[music_channel_id].pause("(Stop cause sound playing)")
                music_user[music_channel_id].state = 3
                # await music_user[self.sound_class.ctx.channel.id ].ctx.channel.send(f':raised_hand: :raised_hand: :raised_hand:  Music interrupt and can\'t be recover, type `/skip` to play the next music')

        logger.info(self.queqed)

        ## Start the sound
        await self._next()  
        
        ## if the sound finished playing
        while self.StartCount:   
            await asyncio.sleep(1)

        ## resume the music
        if (self.ctx.guild.id  in music_user_guild):
            if (music_user[music_channel_id].state == 3):
                music_user[music_channel_id].startTime = lastMusicTime
                await music_user[music_channel_id].pause("(Stop cause sound playing)")



    async def leave(self):
        record_user_guild = [recording[x ].ctx.guild.id for x in recording]
        if (self.ctx.guild.id in record_user_guild):
            record_channel_id = recording[list(recording)[record_user_guild.index(self.ctx.guild.id)]].ctx.channel.id
            await recording[record_channel_id].kill()

        await super().leave()

class BuildSoundSelect():
    def __init__(self,channel_id ,sound_class,*args , **kwargs):
        self.count = 0
        self.sound_class = sound_class
        self.label, self.sounds = self.getsounds(channel_id)
        options = [ discord.SelectOption(label=self.label[i])for i in range(len(self.label))]
        self.views = []

        # self.view = discord.ui.View(timeout=24*60*60) # timeout -> one day
        
        self.view = discord.ui.View(timeout=24*60*60)
        self.views.append(self.view)
        counter = 0
        for i in range(len(options)//24+1):
            if (len(self.label[24*(i):24*(i+1)])!=0):
                this_select = MySelection(self.sound_class,self.label[24*(i):24*(i+1)] ,self.sounds[24*(i):24*(i+1)] ).select
                self.views[-1].add_item(this_select)
                counter += 1
                if(counter==5):
                    self.view = discord.ui.View(timeout=24*60*60)
                    self.views.append(self.view)
                    counter = 0
            

    def getsounds(self,channel_id):
        save_folder = os.path.join("data/attachments", str(channel_id))
        label, file = [], []
        
        files = glob(f'{save_folder}/*.*')
        files.sort(key=os.path.getmtime)

        for path in glob(f'{save_folder}/*.*'):
            if (path.endswith('mp3') or path.endswith('wav') ):
                self.count += 1

                label.append(os.path.basename(path[:-4]))
                file.append( os.path.basename(path) )

        return label, file


        
        # await self.sound_class.clear()
        # await interaction.followup.send_message(f"{self.label[which_chosen]}")
class MySelection:
    def __init__(self,sound_class,label,sound):
        self.sound_class, self.label, self.sounds = sound_class,label,sound
        options = [ discord.SelectOption(label=label[i])for i in range(len(label))]

        self.select = discord.ui.Select(
                placeholder = "All sounds",
                min_values  = 1, 
                max_values  = 1,
                options = options
            )
        
        self.select.callback = self.callback
    async def callback(self, interaction):
        await self.sound_class.clear()
        which_chosen = self.label.index(self.select.values[0])
        await self.sound_class.playSound(self.sounds[which_chosen])

        # self.sound_class.queqed = [(self.sounds[which_chosen],''), ]

        # music_user_guild = [music_user[x].ctx.guild.id for x in music_user]  # store all guild in music_user

        # if (self.sound_class.ctx.guild.id  in music_user_guild):
        #     music_channel_id = music_user[list(music_user)[music_user_guild.index(self.sound_class.ctx.guild.id)]].ctx.channel.id
        #     if (music_user[music_channel_id].state == 1):
        #         await music_user[music_channel_id].pause("(Stop cause sound playing)")
        #         music_user[music_channel_id].state = 3
        #         # await music_user[self.sound_class.ctx.channel.id ].ctx.channel.send(f':raised_hand: :raised_hand: :raised_hand:  Music interrupt and can\'t be recover, type `/skip` to play the next music')

        # logger.info(self.sound_class.queqed)
        # await self.sound_class._next()


def setup(bot):
    bot.add_cog(Sounds(bot))