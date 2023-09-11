from utils.info       import Record_folder, recording, music_user, sound_user, logger
from discord.commands import slash_command, Option
from pydub.silence    import split_on_silence, detect_nonsilent
from discord.ext      import commands
from pydub            import AudioSegment
from .sounds          import SoundBot, match_target_amplitude
from datetime         import datetime
from glob             import glob
from multiprocessing  import Process

import speech_recognition as sr
import threading
import discord
import asyncio
import random
import time
import shutil
import os


class Record(discord.ext.commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="autosound",description="自動偵測語音播放音效版")
    async def autosound(self, ctx):
        await ctx.respond(f"autosound -{ctx.author.mention}")
        logger.info(f"autosound -{ctx.author.name}")
        try:
            if not ctx.author.voice:
                await ctx.respond('you are not connected to a voice channel')
                return
            else:
                channel = ctx.author.voice.channel

            music_user_guild  = [music_user[x].ctx.guild.id for x in music_user]
            sound_user_guild  = [sound_user[x].ctx.guild.id for x in sound_user]  #  use for check if bot is in the sound dict
            

            if (ctx.guild.id in music_user_guild):  # in sound_user
                music_channel_id = music_user[list(music_user)[music_user_guild.index(ctx.guild.id)]].ctx.channel.id
                if ctx.guild.voice_client not in self.bot.voice_clients:
                    await music_user[music_channel_id].kill()
                    voice = await channel.connect()
                else:
                    voice = music_user[music_channel_id].voice
                    await music_user[music_channel_id].pause()
                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)
            elif (ctx.guild.id in recording):
                # await recording[ctx.guild.id].kill()
                # voice = await channel.connect()
                # sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)
                if (recording[ctx.guild.id].alive):
                    sound_user[ctx.channel.id] = SoundBot(channel, recording[ctx.guild.id].voice , ctx, self.bot)
                    return
                else:
                    voice = await channel.connect()
                    sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)
            elif (ctx.guild.id in sound_user_guild):  # in sound_user
                sound_channel_id = sound_user[list(sound_user)[sound_user_guild.index(ctx.guild.id)]].ctx.channel.id
                if ctx.guild.voice_client not in self.bot.voice_clients:
                    await sound_user[music_channel_id].kill()
                    voice = await channel.connect()
                else:
                    voice = sound_user[sound_channel_id].voice
                    await sound_user[sound_channel_id].clear()

                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)
            else:
                voice = await channel.connect()
                sound_user[ctx.channel.id] = SoundBot(channel, voice , ctx, self.bot)


        except Exception as e:
            logger.error(e)


    
        SRS = SoundAssist( os.path.join(Record_folder,str(ctx.guild.id)),voice, ctx,self.bot,sound_user[ctx.channel.id])

        recording.update({ctx.guild.id: SRS})
        
        # await SRS.StartKeepListening()
        await SRS.threadRecord()
        # vc.start_recording(
        #     discord.sinks.WaveSink(),  # The sink type to use.
        #     # discord.Sink(encoding='wav', filters={'time': 0}),
        #     SRS.once_done,  # What to do once done.
        #     ctx.channel  # The channel to disconnect from.
        # )


    @slash_command(name="stop_autosound",description="結束 - 自動偵測語音播放音效版")
    async def stopAutoSounding(self,ctx):
        await ctx.respond(f"stop_autosound -{ctx.author.mention}",delete_after=10)
        await recording[ctx.guild.id].kill()

    

def setup(bot):
    bot.add_cog(Record(bot))

async def speech_to_text(path):
    r = sr.Recognizer() 
    sound = AudioSegment.from_wav(path)
    folder_name = "audio-chunks"
    normalized_sound = match_target_amplitude(sound, -20.0)
    chunk_filename = os.path.join(folder_name, f"chunk.wav")
    audio_chunk = normalized_sound
    audio_chunk.export(chunk_filename, format="wav")
    with sr.AudioFile(chunk_filename) as source:
        try:
            audio_listened = r.record(source)
            try:
                text = r.recognize_google(audio_listened, language = 'zh-tw', show_all=True)
            except Exception as e:
                logger.error(f"speech_to_text(1) {e}")
            try:
                if text['alternative'][0]['confidence'] < 0.7:
                    text['alternative'][0]['transcript'] = "*inaudible*"
                text = text['alternative'][0]['transcript']
            except sr.UnknownValueError as e:
                text = "*inaudible*"
        except Exception as e:
            # logger.error(f"speech_to_text(2) {e}")
            text = ''
        return [text,], ''
    # normalized_sound = match_target_amplitude(sound, -20.0)
    # nonsilent_data = detect_nonsilent(sound, min_silence_len=500, silence_thresh=-50, seek_step=50)
    # folder_name = "audio-chunks"
    # if not os.path.isdir(folder_name):
    #     os.mkdir(folder_name)
    # whole_text = []
    # time_text  = []

    # for i, chunk in enumerate(nonsilent_data, start=1):
    #     this_time = [chunk_ for chunk_ in chunk]
    #     time_text.append(this_time)
    #     audio_chunk  = sound[this_time[0]:this_time[1]]

    #     chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
    #     audio_chunk.export(chunk_filename, format="wav")

    #     with sr.AudioFile(chunk_filename) as source:
    #         try:
    #             audio_listened = r.record(source)
    #             try:
    #                 text = r.recognize_google(audio_listened, language = 'zh-tw', show_all=True)
    #                 if text['alternative'][0]['confidence'] < 0.7:
    #                     text['alternative'][0]['transcript'] = "*inaudible*"
    #                 text = text['alternative'][0]['transcript']
    #             except sr.UnknownValueError as e:
    #                 text = "*inaudible*"
    #             else:                
    #                 whole_text.append(text)
    #         except:
    #             whole_text.append('')
    #             continue
    # return whole_text, time_text


class SoundAssist:
    def __init__(self,saveFolder,voice, ctx,bot,soundClass):
        self.ctx         = ctx
        self.bot         = bot
        self.voice       = voice
        self.alive       = True
        self.soundClass  = soundClass
        self.saveFolder  = saveFolder
        self.channelid   = soundClass.channelid
        self.countdown   = 0
        
        # empty.wav
        self.waitProcess = False
        self.start_time  = datetime.now().strftime('%y-%m-%d-%H-%M-%S')
        self.getsounds(ctx.guild.id)
        os.makedirs(saveFolder,exist_ok=True)

    def getsounds(self,channel_id):
        save_folder = os.path.join("data/attachments", str(channel_id))
        threading.Thread(target=shutil.copyfile,args=("data/empty.wav", save_folder+"/empty.wav")).start()

        label, file = [], []
        for path in glob(f'{save_folder}/*.*'):
            if ('empty.wav' == os.path.basename(path)):
                continue

            if (path.endswith('mp3') or path.endswith('wav')  ):
                label.append(os.path.basename(path[:-4]))
                file.append( os.path.basename(path) )
        # label = sorted(label, key=lambda x: len(x))
        # file  = sorted(file , key=lambda x: len(label[file.index(x)] ))

        self.label, self.file =  label, file

    async def ReConnect(self):
        if not self.alive:
            return
        
        if self.ctx.guild.voice_client not in self.bot.voice_clients:
            self.voice = await self.ctx.author.voice.channel.connect()

    async def StartKeepListening(self):
        def createThread():
            self.bot.loop.create_task(self.threadRecord())
        Process(target=createThread,daemon=True).start()


    async def kill(self):
        self.alive = False
        try:
            await self.voice.disconnect()
        except Exception as e:
            logger.error(e)
        finally:
            if(self.ctx.guild.id in recording) :
                del recording[ self.ctx.guild.id]


            if(self.ctx.channel.id in sound_user) :
                del sound_user[self.ctx.channel.id]

            

    async def threadRecord(self):
        print("Start Keep recording")
        logger.info(f"[*] Start Keep recording in guild : {self.ctx.guild.id}")
        while self.alive :
            if (self.soundClass.state == 1 or self.waitProcess):
                print("wait for process finish or sound finish")
            while self.soundClass.state == 1 or self.waitProcess:
                await asyncio.sleep(1)
            try:
                print("[*] start recording")
                self.voice.start_recording(
                    discord.sinks.WaveSink(),  # The sink type to use.
                    # discord.Sink(encoding='wav', filters={'time': 0}),
                    self.once_done,  # What to do once done.
                    self.ctx.channel
                )
                await asyncio.sleep(3)
                self.voice.stop_recording()
                await asyncio.sleep(0.5)
                print("stop it!")
                self.countdown += 3.5
            except Exception as e:
                await self.check()
                logger.error(f"threadRecord {e}")
                await asyncio.sleep(1)
                
        print("Record Stop")
    
    def IfContinues(self, word1,word2,numbers):
        for i in range(0,len(word1)-numbers):
            for j in range(0,len(word2)-numbers):
                if ( word1[i:i+numbers] == word2[j:j+numbers] ):
                    return True
        return False

    async def once_done(self, sink: discord.sinks, channel: discord.TextChannel, *args):
        self.waitProcess = True
        if not self.alive:
            return
        # recorded_users = [  # A list of recorded users
        #     (await self.bot.fetch_user(user_id)).name
        #     for user_id, audio in sink.audio  _data.items()
        # ]

        # end_time = datetime.now().strftime('%y-%m-%d-%H-%M-%S')
        day_folder =  self.saveFolder
        os.makedirs(day_folder,exist_ok=True)
        
        choseLen, choseFile = 0, None
        try:
            for user_id, audio in sink.audio_data.items():
                this_file = os.path.join(day_folder,f'{user_id}.wav')
                AudioSegment.from_raw(audio.file, format="wav", sample_width=2,frame_rate=48000,channels=2).export(this_file, format='wav')
                result, timeline = await speech_to_text(this_file)
                print("\t",user_id,":",result[0])
                if not all( [len(i)==0 for i in result] ):

                    for eachText in result:
                        if (len(eachText)>=2):
                            for eachSound,eachFile in zip(self.label, self.file):
                                if ( self.IfContinues(eachText,eachSound,2) ):
                                    intersected = list(set(eachText)&set(eachSound.lower()))
                                    thisLen = len(intersected)
                                    print(f"\t\t{thisLen} -> {eachSound}")
                                    if (thisLen > choseLen  or (thisLen == choseLen and random.random()>0.3)):
                                        choseFile = eachFile
                                        choseLen  = thisLen

                        if (len(eachText)==1):
                            for eachSound,eachFile in zip(self.label, self.file):
                                if ( eachText in eachSound ):
                                    print(f"\t\tSingle -> {eachSound}")
                                    if (choseFile):
                                        if (random.random()>0.3):
                                            choseFile = eachFile
                                    else:
                                        choseFile = eachFile

                                        
                threading.Thread(target=os.remove,args=(this_file,)).start()

            if (choseFile and self.soundClass.state == 0):
                await self.soundClass.playSound(choseFile)

            if (self.countdown >300):
                logger.info("[*] Play a empty sound")
                await self.soundClass.playSound("empty.wav")

        except Exception as e:
            logger.error(f"once done {e}")
        finally:
            self.waitProcess = False

        


    async def check(self):
        
        if not self.alive:
            return
        
        await self.ReConnect()

        if (self.ctx.guild.voice_client not in self.bot.voice_clients):
            logger.info("[*] (SoundAssist)  bot not in voice client")
            await self.kill()
            return 
        

        member_count = len(self.ctx.author.voice.channel.voice_states)
        print(f"[*] {self.channelid}, left member : {member_count}")
        if (member_count == 1):
            logger.info(f"[*] (SoundAssist) {self.channelid}, left member : {member_count}")
            logger.info(f"[*] (SoundAssist) {self.channelid}, Music stop cause no one listening")
            await self.kill()
            return
        
